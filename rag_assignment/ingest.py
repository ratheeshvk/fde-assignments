"""Exercise B - chunk, embed (BAAI/bge-small-en-v1.5, 384-d) and store the 30 documents.

Run: python ingest.py [--strategy structure_recursive]
Uses the ADMIN login (ingestion is a privileged, offline job). Re-running replaces
the chunks of the chosen strategy and re-syncs document metadata and ACLs.
"""
from __future__ import annotations

import argparse
import time

import chunkers
from common import DEFAULT_STRATEGY, connect, embed, embedding_text, load_corpus, token_count


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--strategy", choices=chunkers.STRATEGIES, default=DEFAULT_STRATEGY)
    args = p.parse_args()

    started = time.monotonic()
    docs = load_corpus()
    rows = []
    for d in docs:
        for no, c in enumerate(chunkers.run(args.strategy, d["text"], embed_fn=embed)):
            text_for_model = embedding_text(d["title"], c.heading_path, c.text)
            rows.append({"doc": d, "no": no, "chunk": c, "embed_text": text_for_model,
                         "tokens": token_count(text_for_model)})
    print(f"{len(docs)} documents -> {len(rows)} chunks ({args.strategy}); embedding...")
    vectors = []
    for i in range(0, len(rows), 64):
        vectors.extend(embed([r["embed_text"] for r in rows[i:i + 64]]))
        print(f"  embedded {len(vectors)}/{len(rows)}", end="\r")
    print()

    with connect(admin=True) as db, db.transaction():
        for d in docs:
            db.execute("""INSERT INTO k8srag.documents(document_id, title, category, classification, file_name,
                              source_path, source_url, github_url, commit_sha, license, ingested_at)
                          VALUES (%(document_id)s, %(title)s, %(category)s, %(classification)s, %(file_name)s,
                              %(source_path)s, %(source_url)s, %(github_url)s, %(commit_sha)s, %(license)s, now())
                          ON CONFLICT (document_id) DO UPDATE SET title = excluded.title,
                              category = excluded.category, classification = excluded.classification,
                              file_name = excluded.file_name, source_path = excluded.source_path,
                              source_url = excluded.source_url, github_url = excluded.github_url,
                              commit_sha = excluded.commit_sha, license = excluded.license,
                              ingested_at = excluded.ingested_at""", d)
            db.execute("DELETE FROM k8srag.document_acl WHERE document_id = %s", (d["document_id"],))
            for group in d["groups"]:
                db.execute("INSERT INTO k8srag.document_acl(document_id, group_name) VALUES (%s, %s)",
                           (d["document_id"], group))
        db.execute("DELETE FROM k8srag.chunks WHERE chunking_strategy = %s", (args.strategy,))
        with db.cursor() as cur:
            cur.executemany(
                """INSERT INTO k8srag.chunks(document_id, chunking_strategy, chunk_no, heading_path,
                       char_start, char_end, token_count, chunk_text, embedding)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [(r["doc"]["document_id"], args.strategy, r["no"], r["chunk"].heading_path, r["chunk"].start,
                  r["chunk"].end, r["tokens"], r["chunk"].text, v) for r, v in zip(rows, vectors)])
        summary = db.execute("""SELECT d.category, count(DISTINCT d.document_id), count(c.chunk_id)
                                FROM k8srag.documents d
                                LEFT JOIN k8srag.chunks c ON c.document_id = d.document_id
                                     AND c.chunking_strategy = %s
                                GROUP BY d.category ORDER BY d.category""", (args.strategy,)).fetchall()
    for category, n_docs, n_chunks in summary:
        print(f"  {category:<24} {n_docs:>2} documents {n_chunks:>4} chunks")
    print(f"Finished in {time.monotonic() - started:.1f}s. "
          f'Next: python search.py --user priya --question "How does a Deployment manage replicas?"')


if __name__ == "__main__":
    main()
