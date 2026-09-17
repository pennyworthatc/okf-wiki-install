#!/usr/bin/env python3
"""Ingest an immutable source into an OKF Wiki vault. Stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from okf_common import now_iso, slugify, vault_root


def _raw_filename(source: Path, data: bytes) -> str:
    """Create a short human-readable raw filename with a content hash."""
    stem = slugify(source.stem) or "source"
    suffix = source.suffix
    digest = hashlib.sha256(data).hexdigest()[:8]
    return f"{stem}-{digest}{suffix}"


def _append_log(root: Path, entry: str) -> None:
    log_path = root / "log.md"

    if not log_path.exists():
        log_path.write_text("# Log\n\n", encoding="utf-8")

    content = log_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if content.startswith("# Log"):
        content = "# Log\n\n" + entry + content[len("# Log"):].lstrip("\n")
    else:
        content = "# Log\n\n" + entry + content

    log_path.write_text(content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ingest an immutable source into an OKF Wiki vault"
    )
    ap.add_argument(
        "source",
        help="Path to the source file to ingest",
    )
    ap.add_argument(
        "--vault",
        default=None,
        help="Vault path (defaults to OKF_WIKI_VAULT)",
    )
    ap.add_argument(
        "--title",
        default=None,
        help="Human-readable source title",
    )
    ap.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip Git commit",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without modifying the vault",
    )
    args = ap.parse_args()

    root = (
        Path(args.vault).expanduser().resolve()
        if args.vault
        else vault_root()
    )

    raw_dir = root / "raw"

    if not root.is_dir():
        print(f"Vault not found: {root}", file=sys.stderr)
        return 1

    raw_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(args.source).expanduser().resolve()

    if not source_path.is_file():
        print(f"Source not found: {source_path}", file=sys.stderr)
        return 1

    data = source_path.read_bytes()
    raw_name = _raw_filename(source_path, data)
    raw_dest = raw_dir / raw_name
    raw_rel = f"/raw/{raw_name}"

    title = (
        args.title
        or source_path.stem.replace("-", " ").replace("_", " ").strip()
        or "Untitled source"
    )

    ts = now_iso()

    if raw_dest.exists():
        existing = raw_dest.read_bytes()

        if existing == data:
            print(f"Source already ingested: {raw_rel}")
            return 0

        print(
            f"ERROR: destination collision with different content: {raw_dest}",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print(f"[dry-run] copy {source_path} → {raw_dest}")
        print(f"[dry-run] title: {title}")
        print(f"[dry-run] raw: {raw_rel}")
        print("[dry-run] update indexes")
        print("[dry-run] update log")
        if not args.no_commit:
            print("[dry-run] commit")
        return 0

    # 1. Immutable raw copy.
    shutil.copy2(source_path, raw_dest)
    print(f"Copied {source_path} → {raw_rel}")

    # 2. Log the ingest operation.
    entry = f"- {ts} — ingest: {title} ({raw_rel})\n"
    _append_log(root, entry)
    print("Updated log.md")

    # 3. Rebuild indexes.
    from okf_index import main as index_main

    old_argv = sys.argv
    try:
        sys.argv = ["okf_index.py", str(root)]
        rc = index_main()
    finally:
        sys.argv = old_argv

    if rc != 0:
        print("Index rebuild failed.", file=sys.stderr)
        return rc

    # 4. Commit the complete operation.
    if not args.no_commit:
        git_dir = root / ".git"

        if git_dir.is_dir():
            try:
                subprocess.run(
                    ["git", "-C", str(root), "add", "-A"],
                    check=True,
                )

                result = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(root),
                        "commit",
                        "-m",
                        f"ingest: {slugify(title) or 'source'}",
                    ],
                    check=False,
                )

                if result.returncode == 0:
                    print(
                        f"Committed: ingest: "
                        f"{slugify(title) or 'source'}"
                    )
                else:
                    print(
                        "No Git commit created.",
                        file=sys.stderr,
                    )

            except subprocess.CalledProcessError as e:
                print(f"(git skipped: {e})")

    print(f"\nDone. Raw source: {raw_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
