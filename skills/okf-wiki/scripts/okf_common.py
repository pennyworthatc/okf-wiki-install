"""Shared helpers for the local OKF Wiki implementation. Stdlib only."""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VAULT_ENV = "OKF_WIKI_VAULT"

RESERVED_FIELDS = (
    "type",
    "title",
    "description",
    "resource",
    "tags",
    "timestamp",
    "sources",
    "generated",
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?\.md)(?:#[^)]*)?\)")
EXTERNAL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)

MARKER = "<!-- okf:auto-index -->"
MARKER_CLOSE = "<!-- /okf:auto-index -->"

FACTUAL_TYPES = {"Source", "Note"}


# ── Vault ──────────────────────────────────────────────────


def vault_root(path: str | Path | None = None) -> Path:
    """Return the local wiki root.

    Explicit paths take precedence. Otherwise OKF_WIKI_VAULT is used.
    """
    if path is not None:
        return Path(path).expanduser().resolve()

    configured = os.environ.get(VAULT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()

    return Path("/opt/okf-wiki/okf-wiki-vault").resolve()


# ── Time ───────────────────────────────────────────────────


def now_iso() -> str:
    """Current UTC time as ISO 8601."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def valid_iso8601(value: Any) -> bool:
    if not isinstance(value, str):
        return isinstance(value, datetime)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


# ── File helpers ───────────────────────────────────────────


def atomic_write_text(path: Path, text: str) -> None:
    """Write text atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def slugify(value: str) -> str:
    """Derive a short filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", value.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")[:80] or "untitled"


def short_hash(text: str, length: int = 8) -> str:
    """Return a short deterministic SHA-256 hash."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def source_filename(title: str, source_text: str) -> str:
    """Generate a human-readable, collision-resistant raw filename."""
    return f"{slugify(title)}-{short_hash(source_text)}.md"


# ── Frontmatter ────────────────────────────────────────────


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> Any:
    value = value.strip()

    if not value:
        return ""

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item) for item in inner.split(",") if item.strip()]

    return _strip_quotes(value)


def _parse_frontmatter_lines(
    lines: list[str],
    start: int = 0,
    indent: int = 0,
) -> tuple[dict[str, Any], int]:
    """Parse the small YAML subset used by the wiki.

    Supports:
      - scalars
      - lists of scalars
      - lists of mappings
      - nested mappings

    It intentionally does not attempt to implement arbitrary YAML.
    """
    result: dict[str, Any] = {}
    i = start

    while i < len(lines):
        raw = lines[i]

        if not raw.strip():
            i += 1
            continue

        current_indent = len(raw) - len(raw.lstrip(" "))

        if current_indent < indent:
            break
        if current_indent > indent:
            break

        text = raw.strip()

        if text.startswith("- "):
            break

        if ":" not in text:
            i += 1
            continue

        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()

        if value:
            result[key] = _parse_scalar(value)
            i += 1
            continue

        # Empty value: inspect following indented block.
        j = i + 1

        while j < len(lines) and not lines[j].strip():
            j += 1

        if j >= len(lines):
            result[key] = None
            i = j
            continue

        next_raw = lines[j]
        next_indent = len(next_raw) - len(next_raw.lstrip(" "))

        if next_indent <= indent:
            result[key] = None
            i += 1
            continue

        next_text = next_raw.strip()

        # Block list.
        if next_text.startswith("- "):
            items: list[Any] = []

            while j < len(lines):
                raw_item = lines[j]

                if not raw_item.strip():
                    j += 1
                    continue

                item_indent = len(raw_item) - len(raw_item.lstrip(" "))

                if item_indent <= indent:
                    break

                item_text = raw_item.strip()

                if not item_text.startswith("- "):
                    break

                item_text = item_text[2:].strip()

                if ":" not in item_text:
                    items.append(_parse_scalar(item_text))
                    j += 1
                    continue

                item: dict[str, Any] = {}

                item_key, _, item_value = item_text.partition(":")
                item[item_key.strip()] = (
                    _parse_scalar(item_value.strip())
                    if item_value.strip()
                    else None
                )
                j += 1

                # Additional mapping fields for this list item.
                while j < len(lines):
                    extra_raw = lines[j]

                    if not extra_raw.strip():
                        j += 1
                        continue

                    extra_indent = len(extra_raw) - len(extra_raw.lstrip(" "))
                    extra_text = extra_raw.strip()

                    if extra_indent <= indent:
                        break
                    if extra_text.startswith("- "):
                        break
                    if ":" not in extra_text:
                        break

                    extra_key, _, extra_value = extra_text.partition(":")
                    item[extra_key.strip()] = (
                        _parse_scalar(extra_value.strip())
                        if extra_value.strip()
                        else None
                    )
                    j += 1

                items.append(item)

            result[key] = items
            i = j
            continue

        # Nested mapping.
        nested, j = _parse_frontmatter_lines(lines, j, next_indent)
        result[key] = nested
        i = j

    return result, i


def parse_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body)."""
    match = FRONTMATTER_RE.match(md_text)

    if not match:
        return {}, md_text

    lines = match.group(1).splitlines()
    frontmatter, _ = _parse_frontmatter_lines(lines)

    return frontmatter, md_text[match.end():]


def _yaml_scalar(value: Any) -> str:
    """Render a scalar safely for the supported YAML subset."""
    value = str(value)

    if value == "":
        return '""'

    if re.match(r"^[A-Za-z0-9 _./\\:@+-]+$", value):
        return value

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent

    if isinstance(value, dict):
        lines: list[str] = []

        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")

        return lines

    if isinstance(value, list):
        lines: list[str] = []

        for item in value:
            if not isinstance(item, dict):
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
                continue

            if not item:
                lines.append(f"{prefix}- {{}}")
                continue

            first = True

            for key, nested in item.items():
                item_prefix = f"{prefix}- " if first else f"{prefix}  "

                if isinstance(nested, (dict, list)):
                    lines.append(f"{item_prefix}{key}:")
                    lines.extend(_yaml_lines(nested, indent + 4))
                else:
                    lines.append(
                        f"{item_prefix}{key}: {_yaml_scalar(nested)}"
                    )

                first = False

        return lines

    return [f"{prefix}{_yaml_scalar(value)}"]


def serialize_frontmatter(frontmatter: dict[str, Any]) -> str:
    """Serialize frontmatter using the wiki's supported YAML subset."""
    return "---\n" + "\n".join(_yaml_lines(frontmatter)) + "\n---\n"


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    """Render a complete Markdown document."""
    return serialize_frontmatter(frontmatter) + "\n" + body.lstrip()


def bump_timestamp(path: Path) -> None:
    """Update timestamp without flattening nested frontmatter."""
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(text)

    if not frontmatter:
        return

    frontmatter["timestamp"] = now_iso()
    atomic_write_text(path, render_markdown(frontmatter, body))


# ── Search ─────────────────────────────────────────────────


_STOPWORDS: set[str] = {
    "and", "the", "this", "that", "with", "from", "have", "been", "were",
    "they", "their", "them", "will", "would", "could", "should", "about",
    "there", "which", "what", "when", "where", "than", "then", "also",
    "just", "more", "some", "such", "only", "other", "into", "over",
    "very", "after", "before", "because", "between", "through", "during",
    "without", "within", "along", "these", "those", "does", "being", "its",
}


def tokenize_query(query: str) -> list[str]:
    normalized = query.lower()
    normalized = re.sub(r"[\-_./\\]+", " ", normalized)
    normalized = re.sub(r"[\W_]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    seen: set[str] = set()
    tokens: list[str] = []

    for token in normalized.split():
        if len(token) < 2:
            continue
        if token in _STOPWORDS:
            continue
        if token in seen:
            continue

        seen.add(token)
        tokens.append(token)

    return tokens


def _term_hits(text: str, terms: list[str]) -> int:
    if not text:
        return 0

    lowered = text.lower()
    return sum(1 for term in terms if term in lowered)


def search_bundle(
    root: Path,
    query: str,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search all curated pages recursively."""
    concepts = load_bundle(root)
    terms = tokenize_query(query)

    if not terms:
        return []

    scored: list[dict[str, Any]] = []

    for concept in concepts:
        if concept.is_reserved_file:
            continue

        fm = concept.frontmatter
        score = 0

        score += _term_hits(str(fm.get("title", "")), terms) * 6
        score += _term_hits(concept.rel, terms) * 4

        for field_name, weight in (
            ("aliases", 5),
            ("description", 4),
            ("tags", 3),
            ("type", 2),
        ):
            value = fm.get(field_name, "")

            if isinstance(value, list):
                value = " ".join(str(item) for item in value)

            score += _term_hits(str(value), terms) * weight

        score += _term_hits(concept.body, terms)

        if score <= 0:
            continue

        title = str(
            fm.get("title")
            or concept.path.stem
        )

        preview = concept.body.strip()[:200].replace("\n", " ")

        if len(concept.body.strip()) > 200:
            preview += "…"

        scored.append(
            {
                "rel": concept.rel,
                "title": title,
                "type": str(fm.get("type", "page")),
                "description": str(fm.get("description", "")),
                "preview": preview,
                "score": score,
                "path": str(concept.path),
            }
        )

    scored.sort(key=lambda item: (-item["score"], item["rel"]))

    return scored[:max_results]


# ── Markdown sections ──────────────────────────────────────


def _section_range(body: str, name: str) -> dict[str, int] | None:
    heading_re = re.compile(
        rf"^##\s+{re.escape(name)}[ \t]*$",
        re.MULTILINE,
    )

    match = heading_re.search(body)

    if not match:
        return None

    heading_end = match.end()
    content_start = heading_end

    next_heading = re.search(
        r"^##\s+",
        body[content_start:],
        re.MULTILINE,
    )

    content_end = (
        content_start + next_heading.start()
        if next_heading
        else len(body)
    )

    return {
        "heading_start": match.start(),
        "heading_end": heading_end,
        "content_start": content_start,
        "content_end": content_end,
    }


def extract_section(body: str, name: str) -> str | None:
    section = _section_range(body, name)

    if section is None:
        return None

    return body[
        section["content_start"]:section["content_end"]
    ].strip()


def replace_section(body: str, name: str, new_content: str) -> str:
    section = _section_range(body, name)

    if section is None:
        raise ValueError(f"section `## {name}` not found in body")

    before = body[:section["heading_end"]]
    after = body[section["content_end"]:].rstrip()

    if after:
        return (
            f"{before}\n\n"
            f"{new_content.strip()}\n\n"
            f"{after}\n"
        )

    return f"{before}\n\n{new_content.strip()}\n"


def append_to_section(body: str, name: str, text: str) -> str:
    section = _section_range(body, name)

    if section is None:
        raise ValueError(f"section `## {name}` not found in body")

    before = body[:section["content_end"]].rstrip()
    after = body[section["content_end"]:]

    return f"{before}\n\n{text.strip()}\n{after.lstrip()}"


# ── Concepts / links ───────────────────────────────────────


@dataclass
class Concept:
    path: Path
    rel: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    links: list[str] = field(default_factory=list)

    @property
    def is_reserved_file(self) -> bool:
        return self.path.name.lower() in {
            "index.md",
            "log.md",
            "readme.md",
        }

    @property
    def type_tag(self) -> str:
        return str(self.frontmatter.get("type", "page"))


def _rel_target(link: str, from_rel: str) -> str:
    """Normalize a Markdown link to a vault-root-relative path."""
    if EXTERNAL_RE.match(link):
        return link

    if link.startswith("/"):
        return link

    from_dir = "/".join(from_rel.split("/")[:-1])
    combined = (from_dir + "/" + link).lstrip("/")

    parts: list[str] = []

    for segment in combined.split("/"):
        if segment in ("", "."):
            continue

        if segment == "..":
            if parts:
                parts.pop()
        else:
            parts.append(segment)

    return "/" + "/".join(parts)


def load_bundle(root: str | Path) -> list[Concept]:
    """Load all curated Markdown pages recursively.

    Directory names inside `curated/` are intentionally not prescribed.
    """
    root = Path(root).resolve()
    curated_root = root / "curated"

    if not curated_root.is_dir():
        return []

    concepts: list[Concept] = []

    for path in sorted(curated_root.rglob("*.md")):
        rel_parts = path.relative_to(root).parts

        if any(part.startswith(".") for part in rel_parts):
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        frontmatter, body = parse_frontmatter(text)

        rel = "/" + str(
            path.relative_to(root)
        ).replace("\\", "/")

        links = [
            _rel_target(target, rel)
            for target in MD_LINK_RE.findall(body)
        ]

        links = [
            target
            for target in links
            if not EXTERNAL_RE.match(target)
        ]

        concepts.append(
            Concept(
                path=path,
                rel=rel,
                frontmatter=frontmatter,
                body=body,
                links=links,
            )
        )

    return concepts


# ── Provenance / review helpers ────────────────────────────


def source_resources(frontmatter: dict[str, Any]) -> list[str]:
    """Return raw-source resources from frontmatter."""
    sources = frontmatter.get("sources", [])

    if isinstance(sources, str):
        return [sources]

    resources: list[str] = []

    if not isinstance(sources, list):
        return resources

    for item in sources:
        if isinstance(item, dict):
            resource = item.get("resource")
            if resource:
                resources.append(str(resource))
        elif item:
            resources.append(str(item))

    return resources


def has_review_marker(text: str) -> bool:
    return "<!-- REVIEW" in text


def has_contradiction_tag(frontmatter: dict[str, Any]) -> bool:
    tags = frontmatter.get("tags", [])

    if isinstance(tags, str):
        tags = [tags]

    if not isinstance(tags, list):
        return False

    normalized = {
        str(tag).strip().lower()
        for tag in tags
    }

    return "contradict" in normalized
