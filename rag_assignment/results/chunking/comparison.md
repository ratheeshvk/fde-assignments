# Chunking comparison - same 30 Kubernetes documents

Parameters: fixed/recursive size=800, overlap=100; structure_recursive max=1200, overlap=150, min=200; semantic percentile=90.
Sizes are characters of chunk text; tokens are BGE WordPiece tokens of the embedded text (title/heading prefix + chunk).

| Metric | fixed | recursive | structure | semantic | structure_recursive |
|---|---|---|---|---|---|
| Total chunks | 831 | 961 | 478 | 507 | 772 |
| Avg chars | 787 | 613 | 1199 | 1130 | 756 |
| Median chars | 800 | 661 | 775 | 754 | 789 |
| Min chars | 106 | 3 | 86 | 2 | 14 |
| Max chars | 800 | 800 | 13539 | 12205 | 1296 |
| Avg tokens | 207 | 162 | 319 | 293 | 206 |
| Max tokens | 365 | 389 | 4863 | 4796 | 588 |
| Chunks > 512 tokens (truncated) | 0 | 0 | 73 | 86 | 1 |
| Tiny chunks < 150 chars | 5 | 16 | 13 | 75 | 16 |
| Configured overlap | 100 | 100 | 0 | 0 | 150 (oversized sections only) |
| Measured avg overlap (chars) | 100 | 18.1 | 0 | 0 | 15.2 |
| Heading path carried (%) | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 |
| Chunk starts at a heading (%) | 4.0 | 27.9 | 100.0 | 24.1 | 62.6 |
| Clean end: sentence/line (%) | 6.0 | 99.7 | 100.0 | 100.0 | 99.7 |
| Mid-word cut (%) | 84.6 | 0.3 | 0.0 | 0.0 | 0.3 |
| Splits a code block (%) | 11.8 | 2.3 | 0.0 | 2.0 | 1.6 |
| Doc hit@1 (20 questions) | 0.90 | 0.90 | 0.90 | 0.85 | 0.85 |
| Doc hit@5 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Doc MRR | 0.95 | 0.94 | 0.95 | 0.92 | 0.93 |
| Answer-bearing chunk @1 | 0.45 | 0.50 | 0.65 | 0.50 | 0.65 |
| Answer-bearing chunk @3 | 0.65 | 0.80 | 0.80 | 0.85 | 0.90 |
| Avg top-5 context (chars) | 3943 | 3103 | 8168 | 5724 | 3812 |

## Retrieval detail

Each cell is `doc rank / answer rank`: rank of the first chunk from the expected document, and rank of the first chunk from that document containing every answer term (listed in data/eval_questions.json). Lower is better; 1/1 is ideal.

| Question | Expected | fixed | recursive | structure | semantic | structure_recursive |
|---|---|---|---|---|---|---|
| How does a Kubernetes Deployment manage application replicas? (assignment) | APP-deployment | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 1 / 1 |
| What are PersistentVolumes and PersistentVolumeClaims? (assignment) | PLAT-persistent-volumes | 1 / 5 | 1 / 1 | 1 / 2 | 1 / 1 | 1 / 1 |
| What are recommended Kubernetes RBAC practices? (assignment) | SEC-rbac-good-practices | 1 / 1 | 1 / 1 | 1 / 5 | 1 / 1 | 1 / 21 |
| What are the main Kubernetes components? (assignment) | SHR-components | 1 / 1 | 2 / 2 | 1 / 5 | 2 / 2 | 1 / 3 |
| How do I run a Job on a repeating schedule? | APP-cron-jobs | 1 / 4 | 1 / 1 | 1 / 4 | 1 / 12 | 2 / 2 |
| How do I roll back a Deployment to a previous revision? | APP-deployment | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| How does the Horizontal Pod Autoscaler calculate the desired number of replicas? | APP-horizontal-pod-autoscale | 1 / 1 | 1 / 2 | 1 / 1 | 1 / 2 | 1 / 1 |
| How do init containers differ from regular app containers? | APP-init-containers | 1 / 2 | 1 / 4 | 1 / 1 | 1 / 2 | 1 / 1 |
| What stable network identity does a StatefulSet give each Pod? | APP-statefulset | 1 / 6 | 1 / 4 | 1 / 3 | 1 / 1 | 1 / 2 |
| What does the restartPolicy field of a Pod control? | APP-pod-lifecycle | 1 / 1 | 1 / 2 | 1 / 1 | 1 / 3 | 1 / 1 |
| How can I take a point-in-time snapshot of a volume? | PLAT-volume-snapshots | 1 / 2 | 1 / 1 | 1 / 1 | 1 / 5 | 1 / 1 |
| What access modes can a PersistentVolume have, such as ReadWriteOnce? | PLAT-persistent-volumes | 1 / 2 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| Which volume binding mode delays binding until a Pod using the claim is scheduled? | PLAT-storage-classes | 1 / 4 | 1 / 2 | 1 / 1 | 1 / 1 | 1 / 1 |
| What happens to a PersistentVolume when its claim is deleted under the Retain reclaim policy? | PLAT-persistent-volumes | 1 / 4 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| How do I clone an existing PVC using a dataSource? | PLAT-volume-pvc-datasource | 2 / 2 | 1 / 1 | 2 / 2 | 1 / 1 | 2 / 2 |
| What is the difference between the privileged, baseline and restricted pod security levels? | SEC-pod-security-standards | 1 / 1 | 1 / 2 | 1 / 1 | 1 / 1 | 1 / 3 |
| Why is granting the escalate or bind verbs on roles risky? | SEC-rbac-good-practices | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 14 | 1 / 1 |
| Should Secrets be encrypted at rest in etcd? | SEC-secrets-good-practices | 1 / 4 | 1 / 4 | 1 / 1 | 1 / 2 | 1 / 1 |
| Which stages does a request pass through when it reaches the Kubernetes API server? | SEC-controlling-access | 2 / 10 | 3 / 30 | 2 / 21 | 3 / 3 | 2 / 20 |
| How do namespaces isolate groups of resources within a cluster? | SHR-namespaces | 1 / 1 | 1 / 2 | 1 / 1 | 1 / 1 | 1 / 1 |
