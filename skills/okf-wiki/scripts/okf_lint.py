#!/usr/bin/env python3
"""Health checks for an OKF Wiki vault. Stdlib only."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from okf_common import (
    load_bundle,
    parse_frontmatter,
    vault_root,
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _is_external(link: str) -> bool:
    return (
        link.startswith(("http://", "https://", "mailto:", "#"))
        or link.startswith("!")
    )


def _check_links(root: Path, concept, problems: list[str]) -> None:
    for link in LINK_RE.findall(concept.body):
        link = link.split("#", 1)[0].split("?", 1)[0].strip()
        if not link or _is_external(link):
            continue

        if link.startswith("/"):
            target = root / link.lstrip("/")
        else:
            target = concept.path.parent / link

        target = target.resolve()

        if not target.exists():
            problems.append(
                f"broken link: {concept.rel} -> {link}"
            )


def _check_provenance(root: Path, concept, problems: list[str]) -> None:
    sources = concept.frontmatter.get("sources")

    if sources is None:
        return

    if not isinstance(sources, list):
        problems.append(f"invalid sources metadata: {concept.rel}")
        return

    for source in sources:
        if not isinstance(source, dict):
            problems.append(f"invalid source entry: {concept.rel}")
            continue

        resource = source.get("resource")
        if not resource:
            problems.append(f"source missing resource: {concept.rel}")
            continue

        if str(resource).startswith("/"):
            target = root / str(resource).lstrip("/")
        else:
            target = concept.path.parent / str(resource)

        if not target.exists():
            problems.append(
                f"missing provenance: {concept.rel} -> {resource}"
            )


def _check_frontmatter(root: Path, concept, problems: list[str]) -> None:
    try:
        text = concept.path.read_text(encoding="utf-8", errors="replace")
        frontmatter, _ = parse_frontmatter(text)
    except Exception as exc:
        problems.append(f"invalid frontmatter: {concept.rel}: {exc}")
        return

    if "type" not in frontmatter:
        problems.append(f"missing type: {concept.rel}")


def _check_review(concept, problems: list[str]) -> None:
    text = concept.path.read_text(encoding="utf-8", errors="replace")
    if "<!-- REVIEW" in text:
        problems.append(f"review marker: {concept.rel}")


def _check_orphans(root: Path, concepts, problems: list[str]) -> None:
    referenced: set[str] = set()

    for concept in concepts:
        for link in concept.links:
            if link.startswith("/"):
                referenced.add(link.lstrip("/"))
            elif not link.startswith(("http://", "https://")):
                referenced.add(
                    str(
                        (Path(concept.rel).parent / link).as_posix()
                    ).lstrip("./")
                )

    for concept in concepts:
        if concept.rel.startswith("curated/"):
            if concept.rel not in referenced:
                problems.append(f"orphan curated page: {concept.rel}")


def _check_contradictions(concepts, problems: list[str]) -> None:
    for concept in concepts:
        tags = concept.frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        if "contradict" in [str(tag) for tag in tags]:
            problems.append(f"contradiction marked: {concept.rel}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Health-check an OKF Wiki vault")
    ap.add_argument("--vault", default=None, help="Vault path")
    args = ap.parse_args()

    root = vault_root(args.vault) if args.vault else vault_root()

    if not root.is_dir():
        print(f"ERROR: vault not found: {root}")
        return 1

    concepts = [
        c for c in load_bundle(root)
        if not c.is_reserved_file
    ]

    problems: list[str] = []

    for concept in concepts:
        _check_frontmatter(root, concept, problems)
        _check_links(root, concept, problems)
        _check_provenance(root, concept, problems)
        _check_review(concept, problems)

    _check_orphans(root, concepts, problems)
    _check_contradictions(concepts, problems)

    print(f"Vault: {root}")
    print(f"Curated pages checked: {len(concepts)}")
    print(f"Problems found: {len(problems)}")

    if problems:
        print()
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Health check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
