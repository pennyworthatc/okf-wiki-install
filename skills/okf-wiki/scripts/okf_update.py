#!/usr/bin/env python3
"""Record an intentional update to an OKF Wiki page. Stdlib only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from okf_common import (
    atomic_write_text,
    now_iso,
    parse_frontmatter,
    render_markdown,
    vault_root,
)


def _relative_page(root: Path, page: Path) -> str:
    try:
        return "/" + str(page.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(page)


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

    atomic_write_text(log_path, content)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Record an intentional update to an OKF Wiki page"
    )
    ap.add_argument(
        "page",
        help="Path to the page, absolute or vault-relative",
    )
    ap.add_argument(
        "--vault",
        default=None,
        help="Vault path (defaults to OKF_WIKI_VAULT)",
    )
    ap.add_argument(
        "--message",
        default=None,
        help="Log and Git commit message",
    )
    ap.add_argument(
        "--touch-generated",
        action="store_true",
        help="Update generated.at when present",
    )
    ap.add_argument(
        "--no-index",
        action="store_true",
        help="Skip index rebuild",
    )
    ap.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip Git commit",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without modifying files",
    )
    args = ap.parse_args()

    root = (
        Path(args.vault).expanduser().resolve()
        if args.vault
        else vault_root()
    )

    page = Path(args.page).expanduser()

    if not page.is_absolute():
        page = root / page

    page = page.resolve()

    if not page.is_file():
        print(f"Page not found: {page}")
        return 1

    # Do not allow UPDATE to modify files outside the vault.
    try:
        page.relative_to(root)
    except ValueError:
        print(f"ERROR: page is outside vault: {page}")
        return 1

    text = page.read_text(
        encoding="utf-8",
        errors="replace",
    )

    try:
        frontmatter, body = parse_frontmatter(text)
    except Exception as exc:
        print(f"ERROR: invalid frontmatter: {exc}")
        return 1

    ts = now_iso()
    page_rel = _relative_page(root, page)
    message = args.message or f"update: {page_rel}"

    # Only mutate metadata when explicitly requested and when the
    # page already uses the generated.at convention.
    if args.touch_generated:
        generated = frontmatter.get("generated")

        if isinstance(generated, dict):
            generated = dict(generated)
            generated["at"] = ts
            frontmatter["generated"] = generated

        elif generated is not None:
            print(
                "ERROR: generated metadata exists but is not a mapping",
            )
            return 1

    if args.dry_run:
        print(f"[dry-run] update {page_rel}")
        if args.touch_generated:
            print("[dry-run] update generated.at when present")
        if not args.no_index:
            print("[dry-run] rebuild indexes")
        print("[dry-run] update log")
        if not args.no_commit:
            print(f"[dry-run] commit: {message}")
        return 0

    # Write the page only if metadata actually changed.
    new_text = render_markdown(frontmatter, body)

    if new_text != text:
        atomic_write_text(page, new_text)
        print(f"Updated {page_rel}")
    else:
        print(f"No page content change: {page_rel}")

    # Log the intentional operation.
    _append_log(
        root,
        f"- {ts} — {message}\n",
    )
    print("Updated log.md")

    # Rebuild indexes unless explicitly disabled.
    if not args.no_index:
        from okf_index import main as index_main

        old_argv = __import__("sys").argv
        try:
            __import__("sys").argv = ["okf_index.py", str(root)]
            rc = index_main()
        finally:
            __import__("sys").argv = old_argv

        if rc != 0:
            print("Index rebuild failed.")
            return rc

    # Commit the complete operation.
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
                        message,
                    ],
                    check=False,
                )

                if result.returncode == 0:
                    print(f"Committed: {message}")
                else:
                    print("No Git commit created.")

            except subprocess.CalledProcessError as exc:
                print(f"(git skipped: {exc})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
