# OKF Wiki Agent Instructions

Maintain and query this knowledge base. Markdown is canonical. Git provides history, audit, and rollback.

## Structure

* `index.md` — main navigation.
* `log.md` — chronological operation log.
* `raw/` — immutable source material.
* `curated/` — maintained knowledge derived from sources.
Curated subdirectories are implementation-defined. Do not assume fixed category names. Each curated directory should have an `index.md` for navigation.
* `.obsidian/` — optional Obsidian configuration.

Do not create additional knowledge layers without explicit instruction.

## Query

1. Read `index.md`.
2. Follow relevant links in `curated/`.
3. Use `raw/` when curated knowledge is insufficient or source material is explicitly requested.
4. Prefer existing curated knowledge over reprocessing sources.
5. Follow links; do not scan the entire vault unnecessarily.

## Curated knowledge

Use OKF-compatible metadata. Preserve provenance.

```yaml
---
type: Concept
title: ...
description: ...
tags: [...]
sources:
  - id: source-id
    resource: /raw/source-file.md
generated:
  by: ...
  at: ...
---
```

Do not invent sources, claims, or citations.

## Raw sources

Raw files are immutable. Never silently rewrite or replace them.

Use short human-readable filenames and a short hash when needed to prevent collisions.

## Contradictions

Conflicting evidence is valid knowledge.

Never silently resolve, remove, or choose between conflicting claims. Preserve the relevant sources and make the conflict explicit.

Use the `contradict` tag for affected knowledge.

A contradiction is not automatically an error.

## Review

When human attention is needed, add a Markdown review marker:

```markdown
<!-- REVIEW
status: attention
comment: ...
-->
```

Do not silently resolve issues requiring human judgment.

## Knowledge operations

Normal operation:

`ingest → raw → curate/update → curated → update index → update log → Git commit`

Health checks are separate from normal knowledge operations.

## Git

Commit every meaningful knowledge operation using small, descriptive commits.

Preferred prefixes:

* `ingest:`
* `create:`
* `update:`
* `merge:`
* `contradict:`
* `index:`
* `fix:`

Before changing existing knowledge, inspect it, preserve provenance, make the smallest coherent change, and commit it.

Never destroy knowledge merely to make the wiki cleaner.

## Index

Keep `index.md` as the primary navigation entry point.

Update relevant indexes and links when curated knowledge changes.

## Health

Health checks may detect broken links, invalid metadata, missing provenance, orphan concepts, stale indexes, review markers, and contradictions.

Report problems explicitly. Do not silently repair substantive knowledge conflicts.

## Autonomy

Routine operations may be performed autonomously.

Ask only when information is missing, the requested operation conflicts with these rules, or a configured user gate requires approval.

User configuration may define interests, contracts, and gates. Treat them as authoritative.

## References

`references/` contains reference implementations only.

These instructions and the local architecture take precedence.

When substantially changing the workflow, consult the relevant reference implementation first.

## Default rule

Preserve knowledge and provenance. Make uncertainty explicit. Avoid irreversible changes. Leave a Git checkpoint.
