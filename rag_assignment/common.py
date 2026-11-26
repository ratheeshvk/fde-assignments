"""Shared configuration, database connections, embeddings and corpus loading."""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST = DATA_DIR / "manifest.json"
USERS_FILE = DATA_DIR / "users.json"
RESULTS_DIR = ROOT / "results"
EVIDENCE_DIR = ROOT / "evidence"

load_dotenv(ROOT / ".env")
MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_DIM = 384
SCHEMA = "k8srag"
READER_ROLE = os.getenv("READER_ROLE", "k8s_rag_reader")
DEFAULT_STRATEGY = "structure_recursive"


# ---------------------------------------------------------------- database
def _conninfo(*, admin: bool) -> str:
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    url = os.getenv("ADMIN_DATABASE_URL", "")
    if not url:
        raise RuntimeError("Set ADMIN_DATABASE_URL in .env (see .env.example)")
    settings = conninfo_to_dict(url)
    if not admin:
        password = os.getenv("READER_PASSWORD", "")
        if not password:
            raise RuntimeError("Set READER_PASSWORD in .env (see .env.example)")
        settings.update(user=READER_ROLE, password=password)
    return make_conninfo(**settings)


def connect(*, admin: bool = False, autocommit: bool = False, register: bool = True):
    """admin=True -> schema owner (ingestion/admin only); default -> restricted reader."""
    from pgvector.psycopg import register_vector
    from psycopg import connect as pg_connect

    db = pg_connect(_conninfo(admin=admin), autocommit=autocommit)
    if register:
        register_vector(db)
    return db


# ---------------------------------------------------------------- embeddings
@lru_cache(maxsize=1)
def get_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = [v.tolist() for v in get_model().embed(texts, batch_size=32)]
    if any(len(v) != EMBED_DIM for v in vectors):
        raise RuntimeError(f"Expected {EMBED_DIM}-dimensional embeddings from {MODEL}")
    return vectors


@lru_cache(maxsize=1)
def get_tokenizer():
    """Untruncated copy of the model's WordPiece tokenizer, for honest token counts."""
    from tokenizers import Tokenizer

    model = get_model().model
    tokenizer = Tokenizer.from_file(str(Path(model._model_dir) / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def token_count(text: str) -> int:
    return len(get_tokenizer().encode(text).ids)


def embedding_text(title: str, heading_path: str | None, chunk_text: str) -> str:
    """Text actually embedded: document title (+ heading path when the strategy keeps it)."""
    context = heading_path if heading_path else title
    return f"{context}\n\n{chunk_text}"


# ---------------------------------------------------------------- corpus
def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text())


def load_users() -> dict[str, Any]:
    return json.loads(USERS_FILE.read_text())


def doc_id_for(prefix: str, path: str) -> str:
    stem = Path(path).stem
    if stem == "_index":
        stem = Path(path).parent.name
    return f"{prefix}-{stem}"


def public_url(path: str) -> str:
    slug = path[: -len(".md")]
    if slug.endswith("/_index"):
        slug = slug[: -len("/_index")]
    return f"https://kubernetes.io/docs/{slug}/"


_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_TOOLTIP = re.compile(r"\{\{<\s*glossary_tooltip\s+([^>]*?)>\}\}")
_ATTR = re.compile(r'(\w+)="([^"]*)"')
_CODE_SAMPLE = re.compile(r"\{\{%\s*code_sample\s+([^%]*?)%\}\}")
_FEATURE_STATE = re.compile(r"\{\{<\s*feature-state\s+([^>]*?)>\}\}")
_CALLOUT_OPEN = re.compile(r"\{\{[<%]\s*(note|caution|warning)\s*[>%]\}\}")
_HEADING_SHORTCODE = re.compile(r'\{\{%\s*heading\s+"(\w+)"\s*%\}\}')
_HEADING_NAMES = {"whatsnext": "What's next", "prerequisites": "Before you begin",
                  "objectives": "Objectives", "cleanup": "Clean up", "synopsis": "Synopsis"}
_ANY_SHORTCODE = re.compile(r"\{\{[<%].*?[>%]\}\}", re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HEADING_ANCHOR = re.compile(r"^(#{1,6} .*?)\s*\{#[^}]+\}\s*$", re.M)


def _tooltip(match: re.Match) -> str:
    attrs = dict(_ATTR.findall(match.group(1)))
    return attrs.get("text") or attrs.get("term_id", "")


def _feature_state(match: re.Match) -> str:
    attrs = dict(_ATTR.findall(match.group(1)))
    version = attrs.get("for_k8s_version", "")
    state = attrs.get("state", "")
    return f"*Feature state: {state} {version}*".replace("  ", " ") if state else ""


def clean_hugo_markdown(raw: str) -> tuple[dict[str, Any], str]:
    """Split YAML front matter and replace Hugo shortcodes with readable text."""
    front: dict[str, Any] = {}
    match = _FRONT_MATTER.match(raw)
    if match:
        front = yaml.safe_load(match.group(1)) or {}
        raw = raw[match.end():]
    text = _HTML_COMMENT.sub("", raw)
    text = _HEADING_SHORTCODE.sub(lambda m: _HEADING_NAMES.get(m.group(1), m.group(1).title()), text)
    text = _TOOLTIP.sub(_tooltip, text)
    text = _CODE_SAMPLE.sub(
        lambda m: f"[Code sample: {dict(_ATTR.findall(m.group(1))).get('file', '')}]", text
    )
    text = _FEATURE_STATE.sub(_feature_state, text)
    text = _CALLOUT_OPEN.sub(lambda m: f"**{m.group(1).title()}:**", text)
    text = _ANY_SHORTCODE.sub("", text)
    text = _HEADING_ANCHOR.sub(r"\1", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return front, text


def load_corpus() -> list[dict[str, Any]]:
    manifest = load_manifest()
    sha, root = manifest["commit_sha"], manifest["docs_root"]
    docs = []
    for entry in manifest["documents"]:
        category = manifest["categories"][entry["category"]]
        source_path = f"{root}/{entry['path']}"
        file = RAW_DIR / source_path
        if not file.exists():
            raise FileNotFoundError(f"{file} missing - run: python fetch_dataset.py")
        raw = file.read_text(encoding="utf-8")
        front, body = clean_hugo_markdown(raw)
        title = str(front.get("title") or Path(entry["path"]).stem).strip()
        docs.append({
            "document_id": doc_id_for(category["prefix"], entry["path"]),
            "category": entry["category"],
            "classification": category["classification"],
            "groups": category["groups"],
            "title": title,
            "file_name": Path(entry["path"]).name,
            "source_path": source_path,
            "source_url": public_url(entry["path"]),
            "github_url": f"{manifest['source_repo']}/blob/{sha}/{source_path}",
            "commit_sha": sha,
            "license": manifest["license"],
            "raw_chars": len(raw),
            # Title as H1 so structure-aware splitting has a document root.
            "text": f"# {title}\n\n{body}",
        })
    ids = [d["document_id"] for d in docs]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate document IDs in manifest")
    return docs
