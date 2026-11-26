"""Exercise A - run every chunking strategy over the same 30 documents and compare.

Run: python compare_chunking.py [--fixed-size 800 --overlap 100 --max-chars 1200
                                 --section-overlap 150 --percentile 90]

Outputs (results/chunking/):
  comparison.md         size / overlap / heading / boundary / retrieval table
  summary.json          the same numbers, machine readable
  boundary_examples.md  automatically selected good and poor boundaries per strategy
  chunks/<strategy>.jsonl  every chunk, for inspection
No database needed: retrieval quality is measured in memory with the same model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import statistics
import time

import numpy as np

import chunkers
from common import MODEL, RESULTS_DIR, DATA_DIR, ROOT, embed as model_embed, embedding_text, load_corpus, token_count

OUT = RESULTS_DIR / "chunking"
CACHE = ROOT / ".cache" / "embeddings.pkl"
FENCE_LINE = re.compile(r"^\s*(```|~~~)", re.M)
MAX_MODEL_TOKENS = 512
_cache: dict[str, list[float]] = pickle.loads(CACHE.read_bytes()) if CACHE.exists() else {}


def embed(texts: list[str]) -> list[list[float]]:
    """Model embeddings memoised on disk (.cache/) so re-runs only embed new text."""
    keys = [hashlib.sha1(f"{MODEL}\0{t}".encode()).hexdigest() for t in texts]
    missing = list(dict.fromkeys(t for k, t in zip(keys, texts) if k not in _cache))
    if missing:
        for t, v in zip(missing, model_embed(missing)):
            _cache[hashlib.sha1(f"{MODEL}\0{t}".encode()).hexdigest()] = v
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_bytes(pickle.dumps(_cache))
    return [_cache[k] for k in keys]


def boundary_flags(doc: str, chunk: chunkers.Chunk) -> dict[str, bool]:
    end_text = doc.rstrip()
    s, e = chunk.start, chunk.end
    clean_end = e >= len(end_text) or doc[e] == "\n" or (doc[e - 1] in ".!?:" and doc[e].isspace())
    mid_word = (s > 0 and doc[s - 1].isalnum() and doc[s].isalnum()) or (
        e < len(doc) and doc[e - 1].isalnum() and doc[e].isalnum())
    return {
        "clean_end": clean_end,
        "mid_word": mid_word,
        "broken_fence": len(FENCE_LINE.findall(chunk.text)) % 2 == 1,
        "starts_at_heading": chunk.text.lstrip().startswith("#"),
    }


def chunk_corpus(docs, args) -> dict[str, list[dict]]:
    params = {"size": args.fixed_size, "overlap": args.overlap, "max_chars": args.max_chars,
              "section_overlap": args.section_overlap, "percentile": args.percentile}
    results = {}
    for strategy in chunkers.STRATEGIES:
        started = time.monotonic()
        rows = []
        for d in docs:
            pieces = chunkers.run(strategy, d["text"], embed_fn=embed, **params)
            prev_end = None
            for no, c in enumerate(pieces):
                flags = boundary_flags(d["text"], c)
                rows.append({
                    "document_id": d["document_id"], "chunk_no": no,
                    "start": c.start, "end": c.end, "chars": len(c.text),
                    "overlap_prev": max(0, prev_end - c.start) if prev_end is not None else None,
                    "heading_path": c.heading_path, "text": c.text,
                    "embed_text": embedding_text(d["title"], c.heading_path, c.text), **flags,
                })
                prev_end = c.end
        for r in rows:
            r["tokens"] = token_count(r["embed_text"])
        print(f"  {strategy:<20} {len(rows):>5} chunks ({time.monotonic() - started:.1f}s)")
        results[strategy] = rows
    return results


def retrieval_eval(rows: list[dict], questions: list[dict], k: int = 5) -> dict:
    matrix = np.asarray(embed([r["embed_text"] for r in rows]), dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    q = np.asarray(embed([x["question"] for x in questions]), dtype=np.float32)
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    hits1 = hits5 = ans1 = ans3 = 0
    rr, per_question, context_chars = [], [], []
    for i, item in enumerate(questions):
        distances = 1.0 - matrix @ q[i]
        order = np.argsort(distances)
        ranked_docs = [rows[j]["document_id"] for j in order]
        rank = ranked_docs.index(item["expected"]) + 1
        terms = [t.lower() for t in item["answer_terms"]]
        answer_rank = next((n for n, j in enumerate(order, start=1)
                            if rows[j]["document_id"] == item["expected"]
                            and all(t in rows[j]["text"].lower() for t in terms)), len(order))
        hits1 += rank == 1
        hits5 += rank <= k
        ans1 += answer_rank == 1
        ans3 += answer_rank <= 3
        rr.append(1.0 / rank)
        context_chars.append(sum(rows[j]["chars"] for j in order[:k]))
        top = order[0]
        per_question.append({
            "question": item["question"], "expected": item["expected"],
            "first_relevant_rank": rank, "answer_chunk_rank": answer_rank,
            "top1_document": rows[top]["document_id"], "top1_heading": rows[top]["heading_path"],
            "top1_distance": round(float(distances[top]), 4),
        })
    n = len(questions)
    return {"hit@1": hits1 / n, f"hit@{k}": hits5 / n, "mrr": sum(rr) / n,
            "answer@1": ans1 / n, "answer@3": ans3 / n,
            "avg_top5_context_chars": statistics.mean(context_chars), "per_question": per_question}


def summarise(rows: list[dict], configured_overlap) -> dict:
    sizes = [r["chars"] for r in rows]
    tokens = [r["tokens"] for r in rows]
    overlaps = [r["overlap_prev"] for r in rows if r["overlap_prev"] is not None]
    pct = lambda key: 100.0 * sum(bool(r[key]) for r in rows) / len(rows)
    return {
        "total_chunks": len(rows),
        "avg_chars": round(statistics.mean(sizes)), "median_chars": round(statistics.median(sizes)),
        "min_chars": min(sizes), "max_chars": max(sizes),
        "avg_tokens": round(statistics.mean(tokens)), "max_tokens": max(tokens),
        "over_512_tokens": sum(t > MAX_MODEL_TOKENS for t in tokens),
        "tiny_under_150_chars": sum(s < 150 for s in sizes),
        "configured_overlap": configured_overlap,
        "measured_avg_overlap_chars": round(statistics.mean(overlaps), 1) if overlaps else 0,
        "heading_path_carried_pct": round(pct("heading_path"), 1),
        "starts_at_heading_pct": round(pct("starts_at_heading"), 1),
        "clean_end_pct": round(pct("clean_end"), 1),
        "mid_word_cut_pct": round(pct("mid_word"), 1),
        "broken_code_fence_pct": round(pct("broken_fence"), 1),
    }


def pick_examples(rows: list[dict], doc_id: str) -> tuple[dict | None, dict | None, str]:
    in_doc = [r for r in rows if r["document_id"] == doc_id]
    good = next((r for r in in_doc if r["clean_end"] and not r["mid_word"] and not r["broken_fence"]
                 and r["starts_at_heading"] and 300 <= r["chars"] <= 1200), None) or next(
        (r for r in in_doc if r["clean_end"] and not r["mid_word"] and not r["broken_fence"]), None)
    reasons = [("mid-word cut", lambda r: r["mid_word"]),
               ("splits a code block (unbalanced ``` fence)", lambda r: r["broken_fence"]),
               (f"exceeds {MAX_MODEL_TOKENS} tokens, so the model silently truncates it", lambda r: r["tokens"] > MAX_MODEL_TOKENS),
               ("tiny fragment (<150 chars) with little standalone meaning", lambda r: r["chars"] < 150),
               ("ends mid-sentence", lambda r: not r["clean_end"])]
    for reason, test in reasons:
        poor = next((r for r in in_doc if test(r)), None)
        if poor:
            return good, poor, reason
    return good, None, "no poor boundary found in this document"


def snippet(r: dict, n: int = 180) -> str:
    t = r["text"]
    body = t if len(t) <= 2 * n else f"{t[:n]}\n[... {len(t) - 2 * n} chars ...]\n{t[-n:]}"
    return body


def write_reports(summary: dict, results: dict, args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "chunks").mkdir(exist_ok=True)
    for strategy, rows in results.items():
        with (OUT / "chunks" / f"{strategy}.jsonl").open("w") as fh:
            for r in rows:
                fh.write(json.dumps({k: v for k, v in r.items() if k != "embed_text"}, ensure_ascii=False) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    cols = [("Total chunks", "total_chunks"), ("Avg chars", "avg_chars"), ("Median chars", "median_chars"),
            ("Min chars", "min_chars"), ("Max chars", "max_chars"), ("Avg tokens", "avg_tokens"),
            ("Max tokens", "max_tokens"), ("Chunks > 512 tokens (truncated)", "over_512_tokens"),
            ("Tiny chunks < 150 chars", "tiny_under_150_chars"), ("Configured overlap", "configured_overlap"),
            ("Measured avg overlap (chars)", "measured_avg_overlap_chars"),
            ("Heading path carried (%)", "heading_path_carried_pct"),
            ("Chunk starts at a heading (%)", "starts_at_heading_pct"),
            ("Clean end: sentence/line (%)", "clean_end_pct"), ("Mid-word cut (%)", "mid_word_cut_pct"),
            ("Splits a code block (%)", "broken_code_fence_pct"),
            (f"Doc hit@1 ({len(summary['questions'])} questions)", "hit@1"), ("Doc hit@5", "hit@5"),
            ("Doc MRR", "mrr"), ("Answer-bearing chunk @1", "answer@1"), ("Answer-bearing chunk @3", "answer@3"),
            ("Avg top-5 context (chars)", "avg_top5_context_chars")]
    names = list(summary["strategies"])
    ratio_keys = ("hit@1", "hit@5", "mrr", "answer@1", "answer@3")
    lines = ["# Chunking comparison - same 30 Kubernetes documents", "",
             f"Parameters: fixed/recursive size={args.fixed_size}, overlap={args.overlap}; "
             f"structure_recursive max={args.max_chars}, overlap={args.section_overlap}, min=200; "
             f"semantic percentile={args.percentile}.",
             "Sizes are characters of chunk text; tokens are BGE WordPiece tokens of the embedded text "
             "(title/heading prefix + chunk).", "",
             "| Metric | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for label, key in cols:
        vals = []
        for n in names:
            v = summary["strategies"][n].get(key, summary["strategies"][n]["retrieval"].get(key))
            vals.append(f"{v:.2f}" if isinstance(v, float) and key in ratio_keys else
                        f"{v:.0f}" if isinstance(v, float) and key == "avg_top5_context_chars" else str(v))
        lines.append(f"| {label} | " + " | ".join(vals) + " |")
    lines += ["", "## Retrieval detail", "",
              "Each cell is `doc rank / answer rank`: rank of the first chunk from the expected document, and "
              "rank of the first chunk from that document containing every answer term "
              "(listed in data/eval_questions.json). Lower is better; 1/1 is ideal.", "",
              "| Question | Expected | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for i, q in enumerate(summary["questions"]):
        cells = []
        for n in names:
            pq = summary["strategies"][n]["retrieval"]["per_question"][i]
            cells.append(f"{pq['first_relevant_rank']} / {pq['answer_chunk_rank']}")
        marker = " (assignment)" if q.get("assignment") else ""
        lines.append(f"| {q['question']}{marker} | {q['expected']} | " + " | ".join(cells) + " |")
    (OUT / "comparison.md").write_text("\n".join(lines) + "\n")

    ex = ["# Boundary examples (selected automatically from APP-deployment and SEC-pod-security-standards)", ""]
    for strategy, rows in results.items():
        ex.append(f"## {strategy}")
        for doc_id in ("APP-deployment", "SEC-pod-security-standards"):
            good, poor, reason = pick_examples(rows, doc_id)
            if good:
                ex += [f"**Good** - {doc_id} chunk {good['chunk_no']} ({good['chars']} chars, "
                       f"heading: {good['heading_path'] or 'none carried'})", "", "````text", snippet(good), "````", ""]
            if poor:
                ex += [f"**Poor** - {doc_id} chunk {poor['chunk_no']} ({poor['chars']} chars, {poor['tokens']} tokens): "
                       f"{reason}", "", "````text", snippet(poor), "````", ""]
    (OUT / "boundary_examples.md").write_text("\n".join(ex) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--fixed-size", type=int, default=800)
    p.add_argument("--overlap", type=int, default=100)
    p.add_argument("--max-chars", type=int, default=1200)
    p.add_argument("--section-overlap", type=int, default=150)
    p.add_argument("--percentile", type=float, default=90)
    args = p.parse_args()

    docs = load_corpus()
    questions = json.loads((DATA_DIR / "eval_questions.json").read_text())
    print(f"Chunking {len(docs)} documents with {len(chunkers.STRATEGIES)} strategies")
    results = chunk_corpus(docs, args)
    overlap = {"fixed": args.overlap, "recursive": args.overlap, "structure": 0,
               "semantic": 0, "structure_recursive": f"{args.section_overlap} (oversized sections only)"}
    summary = {"documents": len(docs), "questions": questions, "strategies": {}}
    print("Embedding chunks for the retrieval check")
    for strategy, rows in results.items():
        stats = summarise(rows, overlap[strategy])
        stats["retrieval"] = retrieval_eval(rows, questions)
        summary["strategies"][strategy] = stats
        r = stats["retrieval"]
        print(f"  {strategy:<20} chunks={stats['total_chunks']:<5} avg={stats['avg_chars']:<5} "
              f">512tok={stats['over_512_tokens']:<4} midword={stats['mid_word_cut_pct']:<5}% "
              f"heading={stats['heading_path_carried_pct']:<5}% hit@1={r['hit@1']:.2f} mrr={r['mrr']:.2f} "
              f"answer@1={r['answer@1']:.2f} answer@3={r['answer@3']:.2f}")
    write_reports(summary, results, args)
    print(f"Wrote {OUT / 'comparison.md'}, summary.json, boundary_examples.md, chunks/*.jsonl")


if __name__ == "__main__":
    main()
