# OKF Wiki Install

Instructions and tooling to install, restore, and maintain an OKF-compatible LLM wiki.

## Goal

Provide a reproducible installation that allows an AI agent to bootstrap or restore an OKF-compatible LLM wiki on a Linux machine with minimal manual intervention.

The installation is divided into independent phases so that the local wiki can be made operational before optional integrations and migration are configured.

## Installation phases

### 1. Local installation

Install and configure the components required for a functional local wiki:

* OKF-compatible wiki structure
* `raw/` and `curated/` knowledge layers
* agent skills and tasks
* local Quartz WebView
* Git-based versioning

The local installation must be usable without requiring GitHub, Obsidian, or Tailscale.

### 2. Integration

Detect and configure available integrations, including:

* GitHub
* Obsidian
* Tailscale
* LLM/agent capabilities

Integrations should use credentials supplied by the user or execution environment. Secrets must not be stored in this public repository.

### 3. Existing wiki migration

If the user already has a vault, wiki, or other knowledge base:

1. Ask whether an existing knowledge base should be imported.
2. Inspect its structure before modifying anything.
3. Identify curated/concept material and raw/source material.
4. Handle non-standard layouts, including raw material nested inside curated directories.
5. Merge the material into the OKF Wiki structure without silently deleting source material.
6. Preserve provenance where possible.
7. Run OKF validation/linting.
8. Rebuild indexes.
9. Record the migration in the wiki log.
10. Create a Git checkpoint.

Migration should be safe to repeat and should avoid destructive operations unless explicitly required.

### 4. Normal operation

The resulting wiki consists of:

```text
okf-wiki-vault/
├── index.md
├── log.md
├── raw/
├── curated/
└── .obsidian/
```

The Markdown files are the canonical knowledge representation.

The agent should:

* query the curated wiki before consulting raw sources;
* preserve source provenance;
* never silently resolve contradictions;
* use the `contradict` tag when appropriate;
* preserve meaningful Git history;
* create recoverable commits after meaningful knowledge operations.

### 5. Health checks

Validation is separate from ingestion and normal knowledge updates.

A periodic health check should inspect, as applicable:

* OKF frontmatter;
* provenance;
* broken or suspicious links;
* indexes;
* orphaned concepts;
* stale material;
* contradiction markers;
* review markers;
* repository consistency.

Health checks should report problems without treating legitimate contradictions as errors.

Repairs should be explicit, reviewable, and committed separately from unrelated knowledge changes.

## Architecture

The installation separates three repositories:

### `okf-wiki-install`

Public repository containing the reusable installation procedure, scripts, templates, and agent instructions.

### `okf-wiki-vault`

Private repository containing the user's actual knowledge base.

### `okf-wiki-infra`

Private repository containing infrastructure configuration, Ansible automation, encrypted secrets, and infrastructure-related backups.

The installation repository must not contain private knowledge, credentials, server-specific secrets, or personal configuration.

## Design principles

* Markdown is the canonical knowledge format.
* OKF is the metadata and structural standard.
* Git provides history, rollback, and auditability.
* Quartz is a read-oriented WebView, not the canonical knowledge store.
* Obsidian is the primary human editing environment.
* The installation should be reproducible and as idempotent as practical.
* AI agents may operate autonomously when authorized.
* Meaningful operations should leave granular Git checkpoints.
* Contradictory evidence is a valid knowledge state and must not be silently resolved.
* Human review can be represented in Markdown so it remains part of the repository and can be detected by health checks.
* 
