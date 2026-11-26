"""Exercise E - negative tests, live revocation and bypass attempts against RLS.

Run: python test_security.py
Output is also written to evidence/security_tests.txt. Any revoked membership is
restored in a finally block, so the script is safe to re-run.
"""
from __future__ import annotations

import datetime as dt
import re
import sys

import psycopg

from common import DEFAULT_STRATEGY, EVIDENCE_DIR, READER_ROLE, connect, embed
from search import RETRIEVAL_SQL, retrieve

RBAC_Q = "What are recommended Kubernetes RBAC practices?"
DEPLOY_Q = "How does a Kubernetes Deployment manage application replicas?"
RESTRICTED_DOC = "SEC-rbac-good-practices"
LOG: list[str] = []
FAILURES: list[str] = []


def say(line: str = "") -> None:
    print(line)
    LOG.append(line)


def check(label: str, actual, expected) -> None:
    ok = actual == expected
    say(f"{'PASS' if ok else 'FAIL'}  {label}  => {actual!r}")
    if not ok:
        FAILURES.append(label)


def count_visible(reader, user: str | None, doc_id: str | None = None, table: str = "chunks") -> int:
    """Direct SQL lookup (not similarity search) - proves rows are invisible, not just low-ranked."""
    with reader.transaction():
        if user is not None:
            reader.execute("SELECT set_config('app.user_id', %s, true)", (user,))
        where, params = ("WHERE document_id = %s", (doc_id,)) if doc_id else ("", ())
        return reader.execute(f"SELECT count(*) FROM k8srag.{table} {where}", params).fetchone()[0]


def top_docs(reader, user: str | None, vector, k: int = 5) -> list[str]:
    return [r["document_id"] for r in retrieve(reader, user, vector, k)]


def show(reader, user, vector, label) -> list[str]:
    results = retrieve(reader, user, vector, 5)
    say(f"      {label} as {user!r}: {len(results)} chunks")
    for r in results:
        say(f"        {r['document_id']:<30} chunk {r['chunk_no']:<3} dist {r['cosine_distance']:.4f}  {r['source_url']}")
    return [r["document_id"] for r in results]


def fingerprint(admin) -> tuple:
    """Hash of every chunk id + embedding: unchanged => nothing was re-embedded or re-ingested."""
    return admin.execute("""SELECT count(*), max(chunk_id),
                                   md5(string_agg(chunk_id::text || ':' || md5(embedding::text), ',' ORDER BY chunk_id))
                            FROM k8srag.chunks""").fetchone()


def expect_error(reader, label: str, statement: str, user: str = "priya", prep: str | None = None) -> None:
    try:
        with reader.transaction():
            reader.execute("SELECT set_config('app.user_id', %s, true)", (user,))
            if prep:
                reader.execute(prep)
            reader.execute(statement)
        say(f"FAIL  {label}  => statement succeeded")
        FAILURES.append(label)
    except psycopg.Error as exc:
        say(f"PASS  {label}  => {type(exc).__name__}: {str(exc).splitlines()[0]}")


def main() -> None:
    say(f"Security test run {dt.datetime.now().isoformat(timespec='seconds')} | reader role: {READER_ROLE}")
    rbac_vec, deploy_vec = embed([RBAC_Q, DEPLOY_Q])
    with connect(admin=True, autocommit=True) as admin, connect() as reader:
        attrs = admin.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = %s",
                              (READER_ROLE,)).fetchone()
        check("Reader role is NOT superuser and NOT BYPASSRLS", attrs, (False, False))

        say("\n== 1. Authorized user retrieves a restricted document")
        docs = show(reader, "meena", rbac_vec, RBAC_Q)
        check("Meena (security_engineering): top-1 is SEC-rbac-good-practices", docs[:1], [RESTRICTED_DOC])
        check("Meena: direct lookup of SEC-rbac-good-practices finds chunks", count_visible(reader, "meena", RESTRICTED_DOC) > 0, True)
        check("Divya (app + security): RBAC doc visible", count_visible(reader, "divya", RESTRICTED_DOC) > 0, True)

        say("\n== 2. Unauthorized users cannot retrieve that same document")
        for user in ("priya", "arjun"):
            docs = show(reader, user, rbac_vec, RBAC_Q)
            check(f"{user}: no SEC-* document in RBAC search results", any(d.startswith("SEC-") for d in docs), False)
            check(f"{user}: direct SELECT of SEC-rbac-good-practices chunks returns 0",
                  count_visible(reader, user, RESTRICTED_DOC), 0)
            check(f"{user}: document metadata row is hidden too",
                  count_visible(reader, user, RESTRICTED_DOC, "documents"), 0)
        check("arjun cannot see APP-deployment", count_visible(reader, "arjun", "APP-deployment"), 0)
        check("priya cannot see PLAT-persistent-volumes", count_visible(reader, "priya", "PLAT-persistent-volumes"), 0)
        check("meena cannot see APP-deployment", count_visible(reader, "meena", "APP-deployment"), 0)
        check("divya cannot see PLAT-persistent-volumes", count_visible(reader, "divya", "PLAT-persistent-volumes"), 0)
        for user in ("priya", "arjun", "meena", "divya"):
            check(f"{user} can see shared SHR-components", count_visible(reader, user, "SHR-components") > 0, True)

        say("\n== 3. Revoking membership removes access immediately (no re-embedding / re-ingestion)")
        before = fingerprint(admin)
        say(f"      chunk fingerprint before: count={before[0]} max_id={before[1]} hash={before[2]}")
        try:
            admin.execute("DELETE FROM k8srag.user_groups WHERE user_id = 'divya' AND group_name = 'security_engineering'")
            say("      ADMIN: DELETE FROM k8srag.user_groups WHERE user_id='divya' AND group_name='security_engineering'")
            docs = show(reader, "divya", rbac_vec, RBAC_Q)
            check("divya after revoke: no SEC-* document in RBAC search", any(d.startswith("SEC-") for d in docs), False)
            check("divya after revoke: direct SELECT of RBAC doc returns 0", count_visible(reader, "divya", RESTRICTED_DOC), 0)
            check("divya after revoke: still sees APP-deployment (other membership intact)",
                  top_docs(reader, "divya", deploy_vec, 1), ["APP-deployment"])
            after = fingerprint(admin)
            check("chunk/embedding fingerprint unchanged by revocation", after, before)
        finally:
            admin.execute("""INSERT INTO k8srag.user_groups(user_id, group_name)
                             VALUES ('divya', 'security_engineering') ON CONFLICT DO NOTHING""")
            say("      ADMIN: restored divya -> security_engineering")

        say("\n== 4. Restoring the legitimate membership returns access")
        docs = show(reader, "divya", rbac_vec, RBAC_Q)
        check("divya after restore: top-1 is SEC-rbac-good-practices", docs[:1], [RESTRICTED_DOC])
        check("chunk/embedding fingerprint still unchanged after restore", fingerprint(admin), before)
        for action, user, group, when in admin.execute(
                """SELECT action, user_id, group_name, changed_at FROM k8srag.membership_audit
                   WHERE user_id = 'divya' AND group_name = 'security_engineering'
                   ORDER BY audit_id DESC LIMIT 2""").fetchall()[::-1]:
            say(f"      audit: {when:%H:%M:%S.%f} {action:<6} {user} {group}")

        say("\n== 5. Unknown / missing / deactivated identities cannot read protected chunks")
        show(reader, "mallory", rbac_vec, RBAC_Q)
        check("unknown identity 'mallory': total visible chunks", count_visible(reader, "mallory"), 0)
        check("unknown identity 'mallory': total visible documents", count_visible(reader, "mallory", table="documents"), 0)
        check("empty identity '': total visible chunks", count_visible(reader, ""), 0)
        check("identity never set: total visible chunks", count_visible(reader, None), 0)
        check("case/spacing trick 'Priya ' is not priya", count_visible(reader, "Priya "), 0)
        count_visible(reader, "priya")  # sets identity with is_local=true in a committed transaction...
        check("identity does not leak into the next transaction", count_visible(reader, None), 0)
        try:
            admin.execute("UPDATE k8srag.app_users SET is_active = false WHERE user_id = 'priya'")
            check("deactivated user priya: total visible chunks", count_visible(reader, "priya"), 0)
        finally:
            admin.execute("UPDATE k8srag.app_users SET is_active = true WHERE user_id = 'priya'")
        check("reactivated priya sees APP-deployment again", count_visible(reader, "priya", "APP-deployment") > 0, True)

        say("\n== 6. Bypass attempts with the reader login are rejected by PostgreSQL")
        expect_error(reader, "read ACL table directly", "SELECT * FROM k8srag.document_acl")
        expect_error(reader, "read group memberships directly", "SELECT * FROM k8srag.user_groups")
        expect_error(reader, "self-grant a group", "INSERT INTO k8srag.user_groups VALUES ('priya', 'security_engineering')")
        expect_error(reader, "tamper with chunks", "UPDATE k8srag.chunks SET chunk_text = 'x'")
        expect_error(reader, "disable RLS on chunks", "ALTER TABLE k8srag.chunks DISABLE ROW LEVEL SECURITY")
        expect_error(reader, "SET row_security = off", "SELECT count(*) FROM k8srag.chunks",
                     prep="SET LOCAL row_security = off")

        say("\n== 7. Query plan: the RLS filter runs inside the scan, before ranking/LIMIT")
        with reader.transaction():
            reader.execute("SELECT set_config('app.user_id', 'priya', true)")
            plan = [r[0] for r in reader.execute(
                "EXPLAIN (COSTS OFF) " + RETRIEVAL_SQL,
                {"q": rbac_vec, "k": 5, "strategy": DEFAULT_STRATEGY}).fetchall()]
        for line in plan:
            say("      " + re.sub(r"'\[[^']*\]'::vector", "'<query embedding>'::vector", line))
        check("RLS predicate (InitPlan of readable_document_ids) is applied in the chunks scan, below Sort/Limit",
              any("Index Cond" in line or "Filter" in line for line in plan
                  if "document_id = ANY ((InitPlan" in line), True)

    say("\n" + ("ALL CHECKS PASSED" if not FAILURES else f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}"))
    say("Note: --user identities are simulated for the demo; production identity must come from a verified login.")
    EVIDENCE_DIR.mkdir(exist_ok=True)
    (EVIDENCE_DIR / "security_tests.txt").write_text("\n".join(LOG) + "\n")
    if FAILURES:
        sys.exit(1)


if __name__ == "__main__":
    main()
