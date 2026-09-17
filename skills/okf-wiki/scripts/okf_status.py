#!/usr/bin/env python3
"""Show read-only OKF Wiki vault status. Stdlib only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from okf_common import load_bundle, vault_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Show OKF Wiki vault status")
    ap.add_argument("--vault", default=None, help="Vault path")
    args = ap.parse_args()

    root = vault_root(args.vault) if args.vault else vault_root()

    if not root.is_dir():
        print(f"ERROR: vault not found: {root}")
        return 1

    raw_dir = root / "raw"
    curated_dir = root / "curated"

    raw_files = [
        p for p in raw_dir.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)
    ] if raw_dir.is_dir() else []

    concepts = [
        c for c in load_bundle(root)
        if not c.is_reserved_file
    ]

    curated_dirs = []
    if curated_dir.is_dir():
        curated_dirs = [
            p for p in curated_dir.rglob("*")
            if p.is_dir() and not any(part.startswith(".") for part in p.relative_to(root).parts)
        ]

    print(f"Vault: {root}")
    print(f"Raw files: {len(raw_files)}")
    print(f"Curated pages: {len(concepts)}")
    print(f"Curated directories: {len(curated_dirs) + 1}")

    git_dir = root / ".git"
    if git_dir.is_dir():
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            check=False,
        )
        print()
        print("Git:")
        print(result.stdout.rstrip() or "clean")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
