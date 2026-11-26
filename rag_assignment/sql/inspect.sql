-- Admin-only inspection queries (run with psql as the admin login).
\echo '== Documents and chunks per category'
SELECT d.category, d.classification, count(DISTINCT d.document_id) AS documents,
       count(c.chunk_id) AS chunks, min(vector_dims(c.embedding)) AS dims
FROM k8srag.documents d JOIN k8srag.chunks c USING (document_id)
GROUP BY 1, 2 ORDER BY 1;

\echo '== Group memberships'
SELECT u.user_id, u.display_name, u.is_active, string_agg(ug.group_name, ', ' ORDER BY ug.group_name) AS groups
FROM k8srag.app_users u LEFT JOIN k8srag.user_groups ug USING (user_id)
GROUP BY 1, 2, 3 ORDER BY 1;

\echo '== Document ACL (group -> documents)'
SELECT a.group_name, count(*) AS documents, string_agg(a.document_id, ', ' ORDER BY a.document_id) AS document_ids
FROM k8srag.document_acl a GROUP BY 1 ORDER BY 1;

\echo '== RLS status'
SELECT relname, relrowsecurity AS rls_enabled, relforcerowsecurity AS rls_forced
FROM pg_class WHERE relnamespace = 'k8srag'::regnamespace AND relkind = 'r' ORDER BY 1;

\echo '== Policies'
SELECT tablename, policyname, cmd, roles, qual FROM pg_policies WHERE schemaname = 'k8srag';

\echo '== Reader role attributes and table grants'
SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolinherit
FROM pg_roles WHERE rolname = 'k8s_rag_reader';
SELECT table_name, privilege_type FROM information_schema.role_table_grants
WHERE grantee = 'k8s_rag_reader' ORDER BY 1, 2;

\echo '== Visible chunks per identity, as the reader would see them (simulated with SET ROLE)'
SET ROLE k8s_rag_reader;
SELECT set_config('app.user_id', 'priya', false) \g /dev/null
SELECT 'priya' AS identity, count(*) AS visible_chunks, count(DISTINCT document_id) AS visible_documents,
       string_agg(DISTINCT split_part(document_id, '-', 1), ',') AS categories FROM k8srag.chunks;
SELECT set_config('app.user_id', 'arjun', false) \g /dev/null
SELECT 'arjun' AS identity, count(*) AS visible_chunks, count(DISTINCT document_id) AS visible_documents,
       string_agg(DISTINCT split_part(document_id, '-', 1), ',') AS categories FROM k8srag.chunks;
SELECT set_config('app.user_id', 'meena', false) \g /dev/null
SELECT 'meena' AS identity, count(*) AS visible_chunks, count(DISTINCT document_id) AS visible_documents,
       string_agg(DISTINCT split_part(document_id, '-', 1), ',') AS categories FROM k8srag.chunks;
SELECT set_config('app.user_id', 'divya', false) \g /dev/null
SELECT 'divya' AS identity, count(*) AS visible_chunks, count(DISTINCT document_id) AS visible_documents,
       string_agg(DISTINCT split_part(document_id, '-', 1), ',') AS categories FROM k8srag.chunks;
SELECT set_config('app.user_id', 'mallory', false) \g /dev/null
SELECT 'mallory' AS identity, count(*) AS visible_chunks, count(DISTINCT document_id) AS visible_documents,
       string_agg(DISTINCT split_part(document_id, '-', 1), ',') AS categories FROM k8srag.chunks;
RESET ROLE;
