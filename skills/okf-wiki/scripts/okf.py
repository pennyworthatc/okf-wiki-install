#!/usr/bin/env python3
"""Unified CLI for the local OKF Wiki."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

SUBCOMMAND_MAP: dict[str, str] = {
    "bootstrap": "okf_bootstrap.py",
    "init": "okf_init.py",
    "ingest": "okf_ingest.py",
    "update": "okf_update.py",
    "search": "okf_search.py",
    "status": "okf_status.py",
    "index": "okf_index.py",
    "diff": "okf_diff.py",
    "lint": "okf_lint.py",
}

HELP = """OKF Wiki — persistent Markdown knowledge base

Usage: okf <subcommand> [flags]

Subcommands:
  bootstrap [vault]  Bootstrap a local OKF Wiki installation
  init <vault>       Initialize a wiki vault
  ingest <source>    Ingest an immutable raw source
  update <page>      Record an intentional page update
  search <query>     Search curated knowledge
  status             Show vault status
  index              Rebuild curated indexes
  diff               Show pending Git changes
  lint               Run health checks

Knowledge operations:
  ingest → raw → curate/update → curated → index → log → Git

Health checks are separate from normal knowledge operations.
"""

def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(HELP)
        return 0

    sub = sys.argv[1]
    rest = sys.argv[2:]

    if sub not in SUBCOMMAND_MAP:
        print(f"unknown subcommand: {sub!r}", file=sys.stderr)
        print(file=sys.stderr)
        print(HELP, file=sys.stderr)
        return 1

    script_name = SUBCOMMAND_MAP[sub]
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"script not found: {script_path}", file=sys.stderr)
        return 1

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    spec = importlib.util.spec_from_file_location(
        script_name[:-3],
        script_path,
    )
    if spec is None or spec.loader is None:
        print(f"could not load {script_path}", file=sys.stderr)
        return 1

    module = importlib.util.module_from_spec(spec)

    original_argv = sys.argv
    sys.argv = [str(script_path)] + rest

    try:
        spec.loader.exec_module(module)
        if hasattr(module, "main"):
            return module.main()
        return 0
    except SystemExit as exc:
        return exc.code if exc.code is not None else 0
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
