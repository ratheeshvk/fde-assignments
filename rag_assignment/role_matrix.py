"""Exercise D - same question, different identities, different (authorized) results.

Run: python role_matrix.py [--k 5]
Writes evidence/role_matrix.md and evidence/role_matrix.json.

The 'authorized?' column is computed independently of PostgreSQL (from data/users.json
and the manifest ACLs) so it actually checks the RLS result instead of trusting it.
The 'unfiltered' baseline is an admin-only diagnostic and is never shown to users.
"""
from __future__ import annotations

import argparse
import json

from common import DATA_DIR, EVIDENCE_DIR, connect, embed, load_corpus, load_users
from search import RETRIEVAL_SQL, retrieve

IDENTITIES = ["priya", "arjun", "meena", "divya", "mallory"]  # mallory = unknown identity


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--k", type=int, default=5)
    args = p.parse_args()

    questions = [q for q in json.loads((DATA_DIR / "eval_questions.json").read_text()) if q["assignment"]]
    doc_groups = {d["document_id"]: set(d["groups"]) for d in load_corpus()}
    user_groups = {u["user_id"]: set(u["groups"]) for u in load_users()["users"]}
    authorized = lambda user, doc: bool(user_groups.get(user, set()) & doc_groups[doc])

    vectors = embed([q["question"] for q in questions])
    report, violations = [], 0
    md = ["# Exercise D - role-by-role retrieval results", "",
          f"Top-{args.k} chunks per identity, strategy `structure_recursive`, cosine distance (`<=>`, lower is closer).",
          "`Authorized?` is recomputed outside the database from users.json + document ACLs.", ""]
    with connect(admin=True) as admin, connect() as reader:
        for q, vec in zip(questions, vectors):
            with admin.transaction():
                cur = admin.execute(RETRIEVAL_SQL, {"q": vec, "k": args.k, "strategy": "structure_recursive"})
                baseline = [row[0] for row in cur.fetchall()]
            md += [f"## {q['question']}", "", f"Primary area: **{q['area']}** - expected best document "
                   f"`{q['expected']}`. Unfiltered (admin-only) top-{args.k}: {', '.join(baseline)}", ""]
            md += ["| Identity | Rank | Document | Chunk / heading | Cosine distance | Authorized? | Source |",
                   "|---|---|---|---|---|---|---|"]
            entry = {"question": q["question"], "expected": q["expected"], "unfiltered_top": baseline, "users": {}}
            for user in IDENTITIES:
                results = retrieve(reader, user, vec, args.k)
                rows = []
                for rank, r in enumerate(results, start=1):
                    ok = authorized(user, r["document_id"])
                    violations += not ok
                    rows.append({"rank": rank, "document_id": r["document_id"], "chunk_no": r["chunk_no"],
                                 "heading_path": r["heading_path"], "cosine_distance": round(r["cosine_distance"], 4),
                                 "authorized": ok, "source_url": r["source_url"]})
                    md.append(f"| {user} | {rank} | `{r['document_id']}` | {r['chunk_no']} / {r['heading_path']} | "
                              f"{r['cosine_distance']:.4f} | {'yes' if ok else '**NO - LEAK**'} | "
                              f"[{r['title']}]({r['source_url']}) |")
                if not results:
                    md.append(f"| {user} | - | *no authorized chunks* | - | - | n/a | - |")
                withheld = sorted({d for d in baseline if not authorized(user, d)})
                entry["users"][user] = {"results": rows, "withheld_from_unfiltered_top": withheld}
                docs = ", ".join(dict.fromkeys(r["document_id"] for r in rows)) or "(none)"
                print(f"{q['question'][:58]:<58} {user:<8} -> {docs}")
            md.append("")
            report.append(entry)

    md += ["## Summary", "", f"Unauthorized chunks returned across all runs: **{violations}**", ""]
    EVIDENCE_DIR.mkdir(exist_ok=True)
    (EVIDENCE_DIR / "role_matrix.md").write_text("\n".join(md) + "\n")
    (EVIDENCE_DIR / "role_matrix.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Unauthorized chunks returned: {violations}. Wrote evidence/role_matrix.md")
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
