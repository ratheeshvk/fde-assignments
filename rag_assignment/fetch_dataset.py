"""Download the 30 selected Kubernetes docs at the pinned commit into data/raw/.

Run: python fetch_dataset.py
Files keep their original names and directory layout under data/raw/content/en/docs/.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request

from common import MANIFEST, RAW_DIR, load_manifest


def main() -> None:
    manifest = load_manifest()
    sha, root = manifest["commit_sha"], manifest["docs_root"]
    lock = []
    for entry in manifest["documents"]:
        source_path = f"{root}/{entry['path']}"
        url = f"https://raw.githubusercontent.com/kubernetes/website/{sha}/{source_path}"
        target = RAW_DIR / source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read()
        target.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        lock.append({"source_path": source_path, "bytes": len(body), "sha256": digest})
        print(f"  {entry['category']:<24} {source_path} ({len(body)} bytes)")
    (MANIFEST.parent / "manifest.lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    print(f"Downloaded {len(lock)} files at commit {sha[:10]} into {RAW_DIR}")


if __name__ == "__main__":
    main()
