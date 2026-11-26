"""Permission-aware retrieval. Connects as the restricted reader role; PostgreSQL RLS
removes unauthorized chunks inside the query, before ranking and before any LLM.

Run: python search.py --user priya --question "How does a Deployment manage replicas?"

DEMO ONLY: --user simulates the identity a trusted backend would take from a verified
login (OIDC/JWT). End users must never hold the reader credentials themselves.
"""
from __future__ import annotations

import argparse
from typing import Any

from common import DEFAULT_STRATEGY, connect, embed

RETRIEVAL_SQL = """
SELECT c.document_id, d.title, c.chunk_no, c.heading_path, d.source_url, d.github_url,
       (c.embedding <=> %(q)s::vector) AS cosine_distance,
       left(c.chunk_text, 240) AS preview
FROM k8srag.chunks c
JOIN k8srag.documents d ON d.document_id = c.document_id
WHERE c.chunking_strategy = %(strategy)s
ORDER BY c.embedding <=> %(q)s::vector
LIMIT %(k)s
"""


def retrieve(db, user_id: str | None, vector, k: int = 5,
             strategy: str = DEFAULT_STRATEGY) -> list[dict[str, Any]]:
    """Run one retrieval for one identity inside its own transaction."""
    with db.transaction():
        # is_local=true: identity lives only for this transaction, so it cannot leak
        # to the next request on a pooled connection.
        db.execute("SELECT set_config('app.user_id', %s, true)", (user_id or "",))
        cur = db.execute(RETRIEVAL_SQL, {"q": vector, "k": k, "strategy": strategy})
        names = [c.name for c in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]


def run_search(user_id: str, question: str, k: int = 5, strategy: str = DEFAULT_STRATEGY,
               show: bool = True) -> list[dict[str, Any]]:
    vector = embed([question])[0]
    with connect() as db:
        results = retrieve(db, user_id.lower(), vector, k, strategy)
    if show:
        print(f"IDENTITY={user_id} | QUESTION={question!r} | authorized chunks returned={len(results)}")
        for rank, r in enumerate(results, start=1):
            print(f"  {rank}. {r['document_id']:<30} chunk {r['chunk_no']:<3} distance {r['cosine_distance']:.4f}"
                  f"  [{r['heading_path']}]")
            print(f"     {r['source_url']}")
        if not results:
            print("  No authorized chunks. (Nothing is passed to the LLM; answer 'not found / no access'.)")
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Permission-aware vector search (RLS enforced)")
    p.add_argument("--user", required=True, help="demo identity, e.g. priya / arjun / meena / divya")
    p.add_argument("--question", required=True)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--strategy", default=DEFAULT_STRATEGY)
    a = p.parse_args()
    run_search(a.user, a.question, a.k, a.strategy)
