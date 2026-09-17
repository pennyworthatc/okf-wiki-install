#!/usr/bin/env python3
"""Initialize an OKF Wiki vault. Stdlib only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from okf_common import now_iso


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize an OKF Wiki vault")
    ap.add_argument(
        "vault_dir",
        nargs="?",
        default=None,
        help="Vault directory (defaults to OKF_WIKI_VAULT)",
    )
    ap.add_argument("--title", default="OKF Wiki", help="Wiki title")
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args()

    if args.vault_dir:
        root = Path(args.vault_dir).expanduser().resolve()
    else:
        from okf_common import vault_root
        root = vault_root()

    ts = now_iso()

    # Fixed architectural boundaries only.
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "curated").mkdir(parents=True, exist_ok=True)

    # Root navigation.
    root_index = root / "index.md"
    if not root_index.exists():
        root_index.write_text(
            f"""---
type: Index
title: {args.title}
generated:
  by: okf-wiki
  at: {ts}
---

# {args.title}

Knowledge base entry point.

## Curated

- [Curated knowledge](curated/)
""",
            encoding="utf-8",
        )

    # Operation log.
    log = root / "log.md"
    if not log.exists():
        log.write_text(
            f"""# Log

- {ts} — wiki initialized.
""",
            encoding="utf-8",
        )

    # Keep empty raw/curated directories visible to Git.
    raw_gitkeep = root / "raw" / ".gitkeep"
    if not raw_gitkeep.exists():
        raw_gitkeep.write_text("", encoding="utf-8")

    curated_gitkeep = root / "curated" / ".gitkeep"
    if not curated_gitkeep.exists():
        curated_gitkeep.write_text("", encoding="utf-8")

    # Git is optional and idempotent.
    if not args.no_git and not (root / ".git").exists():
        try:
            subprocess.run(
                ["git", "init", "-q"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "branch", "-M", "main"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "add", "-A"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "init: create OKF wiki vault"],
                cwd=root,
                check=False,
            )
        except Exception as e:
            print(f"(git skipped: {e})")

    print(f"Initialized OKF wiki at {root}")
    print(f"  title: {args.title}")
    print("  structure: raw/ + curated/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
