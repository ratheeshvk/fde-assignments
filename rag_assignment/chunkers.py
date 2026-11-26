"""Chunking strategies. Every chunk keeps (start, end) offsets into the source text
so that boundary quality can be measured identically across strategies.

fixed                - every N characters with overlap (mechanical baseline)
recursive            - LangChain RecursiveCharacterTextSplitter (paragraph > line > word > char)
structure            - Markdown heading sections (H1-H3), code-fence aware, no size cap
semantic             - breakpoints where neighbouring-sentence embeddings diverge (percentile)
structure_recursive  - structure first, then recursive split of oversized sections;
                       every piece inherits its heading path (recommended / ingested)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

STRATEGIES = ("fixed", "recursive", "structure", "semantic", "structure_recursive")


@dataclass
class Chunk:
    text: str
    start: int
    end: int
    heading_path: str | None = None


def fixed_size(text: str, size: int = 800, overlap: int = 100) -> list[Chunk]:
    chunks, step = [], size - overlap
    for start in range(0, len(text), step):
        end = min(start + size, len(text))
        chunks.append(Chunk(text[start:end], start, end))
        if end == len(text):
            break
    return chunks


def recursive(text: str, size: int = 800, overlap: int = 100, base: int = 0,
              heading_path: str | None = None) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""], add_start_index=True,
    )
    out = []
    for doc in splitter.create_documents([text]):
        start = base + doc.metadata["start_index"]
        out.append(Chunk(doc.page_content, start, start + len(doc.page_content), heading_path))
    return out


_HEADING = re.compile(r"^(#{1,3}) +(.+?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")


def structure_aware(text: str, max_level: int = 3) -> list[Chunk]:
    """Split at H1..H3 headings (ignoring '#' inside code fences).

    A heading with no body of its own (immediately followed by a sub-heading) is
    merged forward so it never becomes a heading-only chunk.
    """
    sections: list[tuple[int, list[str]]] = []  # (start offset, heading stack)
    stack: list[tuple[int, str]] = []
    in_fence, offset, pending_start = False, 0, None
    lines = text.splitlines(keepends=True)
    body_since_heading = True
    for line in lines:
        if _FENCE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _HEADING.match(line.rstrip("\n"))
        if match and len(match.group(1)) <= max_level:
            level = len(match.group(1))
            stack = [h for h in stack if h[0] < level] + [(level, match.group(2).strip())]
            if sections and not body_since_heading:
                start = sections.pop()[0]  # heading-only section: merge forward
            else:
                start = offset
            sections.append((start, [h[1] for h in stack]))
            body_since_heading = False
        elif line.strip():
            body_since_heading = True
        offset += len(line)
    if not sections:
        return [Chunk(text, 0, len(text), None)]
    if sections[0][0] > 0:  # preamble before first heading
        sections.insert(0, (0, []))
    chunks = []
    for i, (start, path) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else len(text)
        body = text[start:end]
        stripped = body.rstrip()
        if stripped.strip():
            chunks.append(Chunk(stripped, start, start + len(stripped), " > ".join(path) or None))
    return chunks


def _span(text: str, first: Chunk, last: Chunk, heading_path: str | None) -> Chunk:
    body = text[first.start:last.end]
    return Chunk(body, first.start, first.start + len(body), heading_path)


def structure_recursive(text: str, max_chars: int = 1200, overlap: int = 150,
                        min_chars: int = 200) -> list[Chunk]:
    # 1. A tiny section is merged into the sub-section that follows it
    #    ("## Core Components" intro + "### Control Plane Components").
    sections: list[Chunk] = []
    for section in structure_aware(text):
        prev = sections[-1] if sections else None
        if (prev and len(prev.text) < min_chars and prev.heading_path and section.heading_path
                and section.heading_path.startswith(prev.heading_path + " > ")
                and section.end - prev.start <= max_chars):
            sections[-1] = _span(text, prev, section, section.heading_path)
        else:
            sections.append(section)
    # 2. Oversized sections are split recursively; every piece keeps the heading path.
    # 3. A tiny trailing fragment (e.g. a lone ``` fence) is folded into its predecessor.
    out: list[Chunk] = []
    for section in sections:
        if len(section.text) <= max_chars:
            out.append(section)
            continue
        pieces = recursive(section.text, max_chars, overlap, base=section.start,
                           heading_path=section.heading_path)
        merged: list[Chunk] = []
        for piece in pieces:
            if merged and len(piece.text) < min_chars and piece.end - merged[-1].start <= max_chars + min_chars:
                merged[-1] = _span(text, merged[-1], piece, section.heading_path)
            else:
                merged.append(piece)
        out.extend(merged)
    return out


_UNIT_BREAK = re.compile(r"(?<=[.!?])\s+|\n\s*\n")


def _units(text: str) -> list[tuple[int, int]]:
    """Sentence/paragraph spans (start, end) with surrounding whitespace excluded."""
    spans, cursor = [], 0
    for match in _UNIT_BREAK.finditer(text):
        if text[cursor:match.start()].strip():
            spans.append((cursor, match.start()))
        cursor = match.end()
    if text[cursor:].strip():
        spans.append((cursor, len(text.rstrip())))
    return spans


def semantic(text: str, embed_fn: Callable[[list[str]], list[list[float]]],
             percentile: float = 90, buffer: int = 1) -> list[Chunk]:
    """Same algorithm as LangChain SemanticChunker (percentile breakpoints, buffer=1),
    re-implemented on the fastembed model so offsets into the source are preserved."""
    spans = _units(text)
    if len(spans) < 3:
        return [Chunk(text.strip(), 0, len(text.strip()))]
    windows = [
        " ".join(text[s:e] for s, e in spans[max(0, i - buffer): i + buffer + 1])
        for i in range(len(spans))
    ]
    vectors = np.asarray(embed_fn(windows), dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    distances = 1.0 - np.sum(vectors[:-1] * vectors[1:], axis=1)
    threshold = np.percentile(distances, percentile)
    breaks = [i for i, d in enumerate(distances) if d > threshold]
    chunks, first = [], 0
    for b in breaks + [len(spans) - 1]:
        start, end = spans[first][0], spans[b][1]
        chunks.append(Chunk(text[start:end], start, end))
        first = b + 1
    return chunks


def run(strategy: str, text: str, embed_fn=None, **params) -> list[Chunk]:
    if strategy == "fixed":
        return fixed_size(text, params.get("size", 800), params.get("overlap", 100))
    if strategy == "recursive":
        return recursive(text, params.get("size", 800), params.get("overlap", 100))
    if strategy == "structure":
        return structure_aware(text)
    if strategy == "semantic":
        if embed_fn is None:
            raise ValueError("semantic chunking needs embed_fn")
        return semantic(text, embed_fn, params.get("percentile", 90))
    if strategy == "structure_recursive":
        return structure_recursive(text, params.get("max_chars", 1200), params.get("section_overlap", 150))
    raise ValueError(f"Unknown strategy {strategy}")
