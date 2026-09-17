#!/usr/bin/env python3
"""Search the OKF Wiki curated knowledge recursively. Stdlib only."""
from __future__ import annotations

import argparse

from okf_common import load_bundle, vault_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Search curated OKF Wiki knowledge")
    ap.add_argument("query", help="Text to search for")
    ap.add_argument("--vault", default=None, help="Vault path")
    ap.add_argument("--limit", type=int, default=20, help="Maximum results")
    args = ap.parse_args()

    root = vault_root(args.vault) if args.vault else vault_root()
    query = args.query.strip().lower()

    if not query:
        print("ERROR: search query is empty")
        return 1

    concepts = load_bundle(root)
    matches = []

    for concept in concepts:
        fm = concept.frontmatter
        title = str(fm.get("title", ""))
        description = str(fm.get("description", ""))
        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]

        searchable = "\n".join(
            [
                concept.path.as_posix(),
                title,
                description,
                concept.body,
                " ".join(str(tag) for tag in tags),
            ]
        ).lower()

        if query in searchable:
            matches.append((concept, title, description))

    matches.sort(key=lambda item: item[0].path.as_posix())

    if not matches:
        print("No matches.")
        return 0

    for concept, title, description in matches[: args.limit]:
        print(f"{concept.path.relative_to(root)}")
        if title:
            print(f"  title: {title}")
        if description:
            print(f"  {description}")
        print()

    if len(matches) > args.limit:
        print(f"... {len(matches) - args.limit} additional match(es)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
