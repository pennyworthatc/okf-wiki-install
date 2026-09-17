#!/usr/bin/env python3
"""Show pending OKF Wiki changes. Stdlib only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from okf_common import vault_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Show pending OKF Wiki changes")
    ap.add_argument("--vault", default=None, help="Vault path")
    ap.add_argument("--stat", action="store_true", help="Show only diff statistics")
    args = ap.parse_args()

    root = vault_root(args.vault) if args.vault else vault_root()

    if not root.is_dir():
        print(f"ERROR: vault not found: {root}")
        return 1

    if not (root / ".git").is_dir():
        print("No Git repository.")
        return 0

    command = ["git", "-C", str(root), "diff"]
    if args.stat:
        command.append("--stat")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(result.stderr.rstrip())
        return result.returncode

    if result.stdout:
        print(result.stdout, end="")
    else:
        print("Working tree clean.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
