# Week 7: Chunking and Role-Based Security for RAG

A retrieval pipeline over 30 Kubernetes docs pages, stored in Postgres + pgvector, where the results you get depend on which groups you're in. Access is enforced with Row-Level Security (RLS) in the database, not in the app or the prompt.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set ADMIN_DATABASE_URL, READER_ROLE, READER_PASSWORD
docker compose up -d        # only if you need a local pgvector DB
```

Then run:

```bash
python compare_chunking.py   # Exercise A, writes results/chunking/
python bootstrap.py          # schema, RLS, reader role, groups, users
python ingest.py             # Exercise B, loads 772 chunks
python search.py --user priya --question "How does a Kubernetes Deployment manage application replicas?"
python role_matrix.py        # Exercise D, writes evidence/role_matrix.md
python test_security.py      # Exercise E, writes evidence/security_tests.txt
```

Embeddings run locally with fastembed (`BAAI/bge-small-en-v1.5`), so no API keys are needed. The raw docs are already in `data/raw/` (`fetch_dataset.py` re-downloads them).

## Dataset

30 Markdown files from [kubernetes/website](https://github.com/kubernetes/website) at commit [`7c81c4a`](https://github.com/kubernetes/website/tree/7c81c4a67b17aa329f277a53b9e9111fb03b0ede) (CC BY 4.0, © The Kubernetes Authors). I made up the department ownership for this exercise:

- application_engineering: workloads (Deployments, Pods, Jobs, HPA, etc.), 10 docs
- platform_engineering: storage (Volumes, PVs, Storage Classes, Snapshots, etc.), 10 docs
- security_engineering: RBAC, Pod Security Standards, Secrets, etc., 5 docs
- all_employees: overview/concepts pages, 5 docs

The full list is in `data/manifest.json`. Before chunking I strip Hugo front matter, shortcodes and HTML comments. The raw files stay as they are.

## Exercise A: Chunking

I compared five strategies on the same docs:

- `fixed`: 800 chars, 100 overlap
- `recursive`: LangChain recursive splitter, 800/100
- `structure`: split on H1-H3 headings
- `semantic`: split where sentence embeddings drift apart
- `structure_recursive`: split on headings, then break up sections over 1200 chars (the one I ingested)

| | fixed | recursive | structure | semantic | structure_recursive |
|---|---|---|---|---|---|
| Chunks | 831 | 961 | 478 | 507 | 772 |
| Over 512 tokens | 0 | 0 | 73 | 86 | 1 |
| Mid-word cuts | 84.6% | 0.3% | 0% | 0% | 0.3% |
| Answer chunk @1 | 0.45 | 0.50 | 0.65 | 0.50 | 0.65 |
| Answer chunk @3 | 0.65 | 0.80 | 0.80 | 0.85 | 0.90 |

Every strategy found the right document about 85-90% of the time. The real difference was whether the returned chunk actually contained the answer. Some examples of bad boundaries: fixed cuts a table mid-word, and structure/semantic turn the Pod Security Standards table into one ~4,800-token chunk that the model truncates at 512. More are in [`results/chunking/`](results/chunking/comparison.md).

I went with `structure_recursive`. It scored best, every chunk keeps its heading path (e.g. `Persistent Volumes > Lifecycle > Reclaiming`) and fits in the model window, and it's instant compared to semantic chunking. Where it falls short is answers that span several sibling sections. That's only 20 questions I labelled myself, so take the numbers as a rough signal.

## Exercise B: Embeddings

384-dim vectors in a `vector(384)` column, cosine distance search. Ingestion runs as admin. Search runs as the restricted `k8s_rag_reader` role, and the query has no user filter in it because RLS adds one:

```sql
SELECT c.document_id, d.title, c.heading_path, (c.embedding <=> $1::vector) AS distance
FROM k8srag.chunks c JOIN k8srag.documents d USING (document_id)
WHERE c.chunking_strategy = 'structure_recursive'
ORDER BY c.embedding <=> $1::vector
LIMIT 5;
```

## Exercise C: Groups and RLS

Tables: `app_users`, `groups`, `user_groups`, `document_acl`, `documents`, `chunks`, plus a `membership_audit` table filled by a trigger. The reader role can only read `documents` and `chunks`, and both have RLS forced on.

```sql
CREATE POLICY chunks_by_group_membership ON k8srag.chunks FOR SELECT
  USING (document_id = ANY ((SELECT k8srag.readable_document_ids())::text[]));
```

`readable_document_ids()` is a `SECURITY DEFINER` function that joins the user's active groups to the ACL, using `app.user_id`. The backend sets that per transaction with `set_config(..., true)`, so it resets on commit. No user, an unknown user or a deactivated user gets an empty list. Since the filter runs before `ORDER BY ... LIMIT`, restricted chunks never take up slots in the top 5.

Demo users:

| User | Groups | Docs / chunks visible |
|---|---|---|
| priya | app eng | 15 / 460 |
| arjun | platform eng | 15 / 273 |
| meena | security eng | 10 / 157 |
| divya | app + security eng | 20 / 558 |
| mallory | none | 0 / 0 |

Everyone except mallory is also in all_employees. Shared docs are just docs owned by that group, so there's no special case for them.

The backend is the trust boundary here. It holds the reader password and should set `app.user_id` from a real login. In this repo `--user` stands in for that.

## Exercise D: Same question, different users

Full output is in [`evidence/role_matrix.md`](evidence/role_matrix.md). I check every result against `users.json` outside the DB, and none of the 20 runs returned a chunk the user shouldn't see.

A few highlights:

- Deployment question: priya and divya get APP-deployment at distance 0.173. arjun and meena only get shared docs (0.216).
- RBAC question: meena and divya get SEC-rbac-good-practices (0.177). priya and arjun get the shared Overview instead (0.254). The better chunk just doesn't exist for them.
- Components question: all four get the same shared docs.
- mallory gets nothing for any question.

## Exercise E: Security tests

`test_security.py` runs 39 checks and they all pass ([output](evidence/security_tests.txt)). It covers:

- authorized vs unauthorized access to a SEC doc, through search and through a direct `SELECT`
- revoking divya's security group, which takes effect on the next query with embeddings unchanged, then restoring it (both show up in the audit log)
- unknown, empty and deactivated users all get 0 rows
- reader-role bypass attempts: reading the ACL, granting itself a group, disabling RLS, `SET row_security = off`. All of them are rejected.

## Limitations

- Anyone with the reader password can set any `app.user_id`. A signed JWT checked in the DB would be better.
- Admin is a superuser. Ingestion and membership changes should use separate roles.
- No vector index. That's fine at 772 rows, but with HNSW the RLS filter runs after the index scan and can return fewer than k results.
- No relevance threshold, so users always get their closest allowed chunk even if it's a poor match.
- Permissions are per document, not per section. It's also single-tenant, and the eval set is small.

## Reflection

**Is semantic chunking always better?** No. Here it tied recursive at @1 (0.50) and lost to structure-aware chunking (0.65). It produced oversized chunks and tiny fragments, split code blocks, and took minutes to run. It did help when an answer was spread across sections, so it makes sense for unstructured prose. For well-organized docs, the headings are a better guide.

**What if the best document is restricted?** Return only what the user can see: the best allowed chunks if they're relevant, otherwise "nothing found, ask the owning team for access." Don't return the title, a redacted snippet or even "1 result hidden", because any of those tells the user the document exists.

**Why not just tell the LLM to respect permissions?** Once a chunk is in the prompt, it's already leaked. LLMs can be prompt-injected, can paraphrase restricted content, and can't be audited. Filtering in Postgres is deterministic and testable, revocation applies on the next query, and the LLM only ever sees what the user could read anyway.
