#!/usr/bin/env python3
"""Rebuild recursive indexes for an OKF Wiki curated tree. Stdlib only."""
from __future__ import annotations

import argparse
from pathlib import Path

from okf_common import MARKER, MARKER_CLOSE, load_bundle, now_iso


def _display_name(path: Path) -> str:
    return path.name.replace("-", " ").replace("_", " ").title()


def _auto_block(
    directory: Path,
    root: Path,
    pages: list,
    child_dirs: list[Path],
) -> str:
    lines = [MARKER, ""]

    # Child curated directories first.
    for child in child_dirs:
        rel = "/" + str(child.relative_to(root)).replace("\\", "/") + "/"
        lines.append(f"- [{_display_name(child)}]({rel})")

    if child_dirs and pages:
        lines.append("")

    # Then pages in this directory.
    pages.sort(
        key=lambda c: str(
            c.frontmatter.get("title") or c.path.stem
        ).lower()
    )

    for concept in pages:
        title = concept.frontmatter.get("title") or concept.path.stem
        rel = "/" + str(concept.path.relative_to(root)).replace("\\", "/")
        desc = concept.frontmatter.get("description")

        entry = f"- [{title}]({rel})"
        if desc:
            entry += f" — {desc}"

        lines.append(entry)

    lines.extend(["", MARKER_CLOSE, ""])
    return "\n".join(lines)


def _merge_auto_block(existing: str, auto_block: str) -> str:
    if MARKER in existing and MARKER_CLOSE in existing:
        before, _, rest = existing.partition(MARKER)
        _, _, after = rest.partition(MARKER_CLOSE)

        head = before.rstrip() + "\n\n"
        tail = after.lstrip("\n")

        return head + auto_block + ("\n" + tail if tail else "")

    if MARKER in existing:
        head = existing.split(MARKER, 1)[0].rstrip() + "\n\n"
        return head + auto_block

    return existing.rstrip() + "\n\n" + auto_block


def _new_index(directory: Path) -> str:
    title = _display_name(directory)
    return (
        "---\n"
        "type: Index\n"
        f"title: {title}\n"
        "generated:\n"
        "  by: okf-wiki\n"
        f"  at: {now_iso()}\n"
        "---\n\n"
        f"# {title}\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rebuild recursive OKF curated indexes"
    )
    ap.add_argument(
        "vault_dir",
        nargs="?",
        default=None,
        help="Vault directory (defaults to OKF_WIKI_VAULT)",
    )
    ap.add_argument("--vault", dest="vault_opt", default=None, help="Vault directory (defaults to OKF_WIKI_VAULT)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.vault_dir or args.vault_opt:
        root = Path(args.vault_opt or args.vault_dir).expanduser().resolve()
    else:
        from okf_common import vault_root
        root = vault_root()

    curated = root / "curated"

    if not curated.is_dir():
        print(f"ERROR: curated directory does not exist: {curated}")
        return 1

    # Discover every curated directory, regardless of its name.
    directories = sorted(
        [curated] + [
            p for p in curated.rglob("*")
            if p.is_dir() and not p.name.startswith(".")
        ],
        key=lambda p: (len(p.parts), str(p).lower()),
    )

    concepts = load_bundle(root)

    pages_by_dir: dict[Path, list] = {d: [] for d in directories}

    for concept in concepts:
        parent = concept.path.parent

        if parent in pages_by_dir and not concept.is_reserved_file:
            pages_by_dir[parent].append(concept)

    changed = 0

    for directory in directories:
        child_dirs = sorted(
            [
                p for p in directory.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            ],
            key=lambda p: p.name.lower(),
        )

        pages = pages_by_dir.get(directory, [])

        idx_path = directory / "index.md"

        if idx_path.exists():
            existing = idx_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            new_content = _merge_auto_block(
                existing,
                _auto_block(directory, root, pages, child_dirs),
            )
        else:
            new_content = _new_index(directory) + _auto_block(
                directory,
                root,
                pages,
                child_dirs,
            )

        if args.dry_run:
            print(
                f"[dry-run] {idx_path} "
                f"({len(child_dirs)} directories, {len(pages)} pages)"
            )
            continue

        if (
            not idx_path.exists()
            or idx_path.read_text(
                encoding="utf-8",
                errors="replace",
            ) != new_content
        ):
            idx_path.write_text(new_content, encoding="utf-8")
            changed += 1
            print(
                f"updated {idx_path} "
                f"({len(child_dirs)} directories, {len(pages)} pages)"
            )

    if not args.dry_run:
        print(f"Rebuilt indexes. Changed: {changed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
