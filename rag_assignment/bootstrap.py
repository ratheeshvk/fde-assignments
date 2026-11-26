"""One-time, idempotent setup: schema + RLS, restricted reader role, groups and demo users.

Run: python bootstrap.py   (uses ADMIN_DATABASE_URL; never run retrieval as this login)
"""
from __future__ import annotations

import os

from psycopg import sql

from common import READER_ROLE, ROOT, connect, load_users


def main() -> None:
    password = os.getenv("READER_PASSWORD", "")
    if not password:
        raise RuntimeError("READER_PASSWORD is missing in .env")
    users = load_users()
    with connect(admin=True, register=False) as db:
        db.execute((ROOT / "sql" / "schema.sql").read_text())
        dbname = db.info.dbname
        role = sql.Identifier(READER_ROLE)
        exists = db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (READER_ROLE,)).fetchone()
        verb = "ALTER" if exists else "CREATE"
        db.execute(sql.SQL(verb + " ROLE {} WITH LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE "
                           "NOINHERIT PASSWORD {}").format(role, sql.Literal(password)))
        db.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA k8srag FROM {}").format(role))
        db.execute(sql.SQL("REVOKE ALL ON ALL FUNCTIONS IN SCHEMA k8srag FROM {}").format(role))
        db.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(dbname), role))
        db.execute(sql.SQL("GRANT USAGE ON SCHEMA k8srag TO {}").format(role))
        # Least privilege: read-only on the two RLS-protected tables, nothing else.
        db.execute(sql.SQL("GRANT SELECT ON k8srag.chunks, k8srag.documents TO {}").format(role))
        db.execute(sql.SQL("GRANT EXECUTE ON FUNCTION k8srag.readable_document_ids(), "
                           "k8srag.current_app_user() TO {}").format(role))

        for name, description in users["groups"].items():
            db.execute("""INSERT INTO k8srag.groups(group_name, description) VALUES (%s, %s)
                          ON CONFLICT (group_name) DO UPDATE SET description = excluded.description""",
                       (name, description))
        for u in users["users"]:
            db.execute("""INSERT INTO k8srag.app_users(user_id, display_name, is_active) VALUES (%s, %s, true)
                          ON CONFLICT (user_id) DO UPDATE SET display_name = excluded.display_name,
                          is_active = true""", (u["user_id"], u["display_name"]))
            db.execute("DELETE FROM k8srag.user_groups WHERE user_id = %s AND NOT (group_name = ANY(%s))",
                       (u["user_id"], u["groups"]))
            for group in u["groups"]:
                db.execute("""INSERT INTO k8srag.user_groups(user_id, group_name) VALUES (%s, %s)
                              ON CONFLICT DO NOTHING""", (u["user_id"], group))
        rows = db.execute("""SELECT u.user_id, string_agg(ug.group_name, ', ' ORDER BY ug.group_name)
                             FROM k8srag.app_users u LEFT JOIN k8srag.user_groups ug USING (user_id)
                             GROUP BY u.user_id ORDER BY u.user_id""").fetchall()
    print(f"Schema k8srag ready in database {dbname}; reader role {READER_ROLE} (NOSUPERUSER, NOBYPASSRLS)")
    for user_id, groups in rows:
        print(f"  {user_id:<6} -> {groups}")
    print("Next: python ingest.py")


if __name__ == "__main__":
    main()
