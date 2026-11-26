-- Run as the schema owner / admin (bootstrap.py does this). Idempotent.
-- The restricted reader role is created and granted by bootstrap.py.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS k8srag;
REVOKE ALL ON SCHEMA k8srag FROM PUBLIC;

-- ------------------------------------------------------------ identities
CREATE TABLE IF NOT EXISTS k8srag.groups (
    group_name  text PRIMARY KEY,
    description text NOT NULL
);
CREATE TABLE IF NOT EXISTS k8srag.app_users (
    user_id      text PRIMARY KEY,
    display_name text NOT NULL,
    is_active    boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS k8srag.user_groups (
    user_id    text NOT NULL REFERENCES k8srag.app_users(user_id) ON DELETE CASCADE,
    group_name text NOT NULL REFERENCES k8srag.groups(group_name) ON DELETE CASCADE,
    granted_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, group_name)
);
CREATE TABLE IF NOT EXISTS k8srag.membership_audit (
    audit_id   bigserial PRIMARY KEY,
    action     text NOT NULL,
    user_id    text NOT NULL,
    group_name text NOT NULL,
    changed_by text NOT NULL DEFAULT current_user,
    changed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

-- ------------------------------------------------------------ content
CREATE TABLE IF NOT EXISTS k8srag.documents (
    document_id    text PRIMARY KEY,
    title          text NOT NULL,
    category       text NOT NULL,
    classification text NOT NULL CHECK (classification IN ('shared', 'restricted')),
    file_name      text NOT NULL,
    source_path    text NOT NULL,          -- path inside kubernetes/website
    source_url     text NOT NULL,          -- published page on kubernetes.io
    github_url     text NOT NULL,          -- file at the pinned commit
    commit_sha     text NOT NULL,
    license        text NOT NULL,
    ingested_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS k8srag.document_acl (
    document_id text NOT NULL REFERENCES k8srag.documents(document_id) ON DELETE CASCADE,
    group_name  text NOT NULL REFERENCES k8srag.groups(group_name),
    PRIMARY KEY (document_id, group_name)
);
CREATE TABLE IF NOT EXISTS k8srag.chunks (
    chunk_id          bigserial PRIMARY KEY,
    document_id       text NOT NULL REFERENCES k8srag.documents(document_id) ON DELETE CASCADE,
    chunking_strategy text NOT NULL,
    chunk_no          integer NOT NULL,
    heading_path      text,
    char_start        integer NOT NULL,
    char_end          integer NOT NULL,
    token_count       integer NOT NULL,
    chunk_text        text NOT NULL,
    embedding         vector(384) NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunking_strategy, chunk_no)
);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON k8srag.chunks(document_id);
CREATE INDEX IF NOT EXISTS acl_group_idx ON k8srag.document_acl(group_name);

-- ------------------------------------------------------------ audit trigger
CREATE OR REPLACE FUNCTION k8srag.audit_membership() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, k8srag AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO k8srag.membership_audit(action, user_id, group_name) VALUES ('GRANT', NEW.user_id, NEW.group_name);
    RETURN NEW;
  END IF;
  INSERT INTO k8srag.membership_audit(action, user_id, group_name) VALUES ('REVOKE', OLD.user_id, OLD.group_name);
  RETURN OLD;
END $$;
DROP TRIGGER IF EXISTS user_groups_audit ON k8srag.user_groups;
CREATE TRIGGER user_groups_audit AFTER INSERT OR DELETE ON k8srag.user_groups
FOR EACH ROW EXECUTE FUNCTION k8srag.audit_membership();

-- ------------------------------------------------------------ authorization
-- Identity of the current request, set by the trusted backend with
-- set_config('app.user_id', <verified id>, true) - transaction-local.
CREATE OR REPLACE FUNCTION k8srag.current_app_user() RETURNS text
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.user_id', true), '')
$$;

-- SECURITY DEFINER: evaluates ACL x membership with the owner's rights, so the
-- reader role never needs (or gets) SELECT on users / groups / ACL tables.
-- Unknown, inactive or missing identities resolve to an empty array.
CREATE OR REPLACE FUNCTION k8srag.readable_document_ids() RETURNS text[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, k8srag AS $$
  SELECT coalesce(array_agg(DISTINCT a.document_id), '{}')
  FROM k8srag.document_acl a
  JOIN k8srag.user_groups ug ON ug.group_name = a.group_name
  JOIN k8srag.app_users u   ON u.user_id = ug.user_id AND u.is_active
  WHERE u.user_id = k8srag.current_app_user()
$$;
REVOKE ALL ON FUNCTION k8srag.readable_document_ids() FROM PUBLIC;
REVOKE ALL ON FUNCTION k8srag.current_app_user() FROM PUBLIC;

-- RLS on BOTH tables the reader can see. FORCE makes it apply to the table
-- owner too (superusers and BYPASSRLS roles are still exempt - never use them
-- for retrieval). The scalar sub-select is evaluated once per query (InitPlan).
ALTER TABLE k8srag.chunks    ENABLE ROW LEVEL SECURITY;
ALTER TABLE k8srag.chunks    FORCE  ROW LEVEL SECURITY;
ALTER TABLE k8srag.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE k8srag.documents FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS chunks_by_group_membership ON k8srag.chunks;
CREATE POLICY chunks_by_group_membership ON k8srag.chunks
  FOR SELECT USING (document_id = ANY ((SELECT k8srag.readable_document_ids())::text[]));

DROP POLICY IF EXISTS documents_by_group_membership ON k8srag.documents;
CREATE POLICY documents_by_group_membership ON k8srag.documents
  FOR SELECT USING (document_id = ANY ((SELECT k8srag.readable_document_ids())::text[]));
