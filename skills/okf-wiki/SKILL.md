# OKF Wiki Skill

Local, Git-backed Markdown knowledge base using the OKF model.

## Purpose

Use this skill to maintain and query a persistent knowledge base.

Markdown files are canonical. Git provides history, audit, and rollback.

## Structure

* `index.md` — root navigation.
* `log.md` — chronological operation log.
* `raw/` — immutable source material.
* `curated/` — maintained knowledge derived from sources.
* `curated/**/index.md` — navigation indexes for curated directories.
* `.obsidian/` — optional Obsidian configuration.

The curated hierarchy is flexible. Do not assume fixed category names.

## Operations

### INIT

Initialize a new vault.

Creates:

* `raw/`
* `curated/`
* root `index.md`
* root `log.md`

May initialize Git when requested.

### INGEST

Add a source to `raw/`.

Rules:

* Raw sources are immutable.
* Use a short human-readable name plus a short content hash.
* Detect duplicate content.
* Do not silently replace an existing source.
* Update the log.
* Rebuild relevant indexes.
* Commit the complete operation unless explicitly disabled.

Ingest does not automatically create curated knowledge or run health checks.

### UPDATE

Record an intentional change to an existing curated page.

Rules:

* Inspect the existing page first.
* Preserve provenance and unrelated content.
* Make the smallest coherent change.
* Update indexes and the log as appropriate.
* Commit the operation unless explicitly disabled.

### SEARCH

Search existing curated knowledge before processing raw sources.

Search recursively through curated directories.

Prefer existing curated knowledge over reprocessing source material.

### STATUS

Report basic vault state:

* vault location
* raw source count
* curated page count
* curated directory count
* Git branch and working-tree state

Status is read-only.

### INDEX

Rebuild navigation indexes recursively.

For every curated directory:

* maintain an `index.md`;
* list child directories;
* list curated pages;
* preserve manually written content outside the generated index section.

Do not assume specific curated directory names.

### DIFF

Show pending Git changes.

This operation is read-only.

### LINT / HEALTH

Check knowledge-base integrity independently of normal knowledge operations.

Checks may include:

* malformed frontmatter;
* missing required metadata;
* broken Markdown links;
* missing or unresolved provenance;
* orphan curated pages;
* duplicate or near-duplicate pages;
* contradiction markers;
* review markers.

Health checks report problems. They must not silently rewrite substantive knowledge.

A contradiction is a valid knowledge state and is not automatically an error.

## Query-first behavior

When answering a knowledge query:

1. Read the root `index.md`.
2. Follow relevant curated indexes and links.
3. Use existing curated knowledge first.
4. Consult `raw/` when curated knowledge is insufficient or source material is explicitly requested.
5. Follow links rather than scanning the entire vault unnecessarily.

## Provenance

Curated knowledge should preserve source provenance.

Example:

```yaml
---
type: Concept
title: Example concept
description: Example description.
tags:
  - example
sources:
  - id: source-id
    resource: /raw/example-source-abc123.md
generated:
  by: okf-wiki
  at: 2026-01-01T00:00:00Z
---
```

Do not invent sources, claims, or citations.

## Contradictions

Conflicting evidence must remain explicit.

Never silently:

* resolve a contradiction;
* remove one side of conflicting evidence;
* choose one source without documenting the conflict.

Use the `contradict` tag when appropriate.

## Review

When human attention is required, use:

<!-- REVIEW
status: attention
comment: ...
-->

Do not silently resolve issues requiring human judgment.

## Git

Make meaningful knowledge operations into small, descriptive commits.

Preferred prefixes:

* `ingest:`
* `create:`
* `update:`
* `merge:`
* `contradict:`
* `index:`
* `fix:`

Preserve knowledge and provenance.

Avoid irreversible changes.

## Autonomy

Routine knowledge operations may be performed autonomously.

Ask for clarification only when required information is missing, an operation conflicts with the configured rules, or a configured user gate requires approval.

User-specific interests, contracts, and gates belong to the local/private configuration, not to this public skill definition.

## References

Reference implementations are documentation and comparison material only.

The local implementation and its configured rules take precedence.
