#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
INSTALLER_ROOT = SKILL_DIR.parent.parent

DEFAULT_VAULT = Path(
    os.environ.get("OKF_WIKI_VAULT", "/opt/okf-wiki/okf-wiki-vault")
)


def run(command, cwd=None):
    print(f"+ {' '.join(str(x) for x in command)}")
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(str(x) for x in command)}"
        )


def ask_list(label):
    print()
    print(label)
    print("Enter one item per line. Submit an empty line when finished.")

    values = []
    while True:
        value = input("> ").strip()
        if not value:
            break
        values.append(value)

    return values


def save_config(vault, interests, contracts, gates):
    config_dir = vault / ".okf-wiki"
    config_dir.mkdir(parents=True, exist_ok=True)

    config = config_dir / "config.yaml"

    lines = [
        "# Local OKF Wiki configuration.",
        "# This file contains installation-specific/user-specific settings.",
        "",
    ]

    for key, values in (
        ("interests", interests),
        ("contracts", contracts),
        ("gates", gates),
    ):
        if values:
            lines.append(f"{key}:")
            for item in values:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: []")
        lines.append("")

    config.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(config, 0o600)

    return config

def ensure_gitignore(vault):
    gitignore = vault / ".gitignore"

    existing = ""
    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")

    entry = ".okf-wiki/config.yaml"

    if entry not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += entry + "\n"
        gitignore.write_text(existing, encoding="utf-8")


def install_agents(vault):
    source = INSTALLER_ROOT / "AGENTS.md"
    destination = vault / "AGENTS.md"

    if not source.exists():
        raise RuntimeError(f"Installer AGENTS.md not found: {source}")

    if destination.exists():
        raise RuntimeError(
            f"AGENTS.md already exists in fresh-install target: {destination}"
        )

    destination.write_text(
        source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def expose_skill(vault):
    local_dir = vault / ".okf-wiki"
    local_dir.mkdir(parents=True, exist_ok=True)

    link = local_dir / "skill"

    if link.exists() or link.is_symlink():
        raise RuntimeError(f"Skill exposure already exists: {link}")

    link.symlink_to(SKILL_DIR, target_is_directory=True)


def create_git_checkpoint(vault):
    git_dir = vault / ".git"

    if not git_dir.is_dir():
        return False

    run(["git", "add", "-A"], cwd=vault)

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=vault,
    )

    if result.returncode == 0:
        return False

    run(
        [
            "git",
            "commit",
            "-m",
            "bootstrap: initialize OKF Wiki",
        ],
        cwd=vault,
    )

    return True


def is_existing_installation(vault):
    if not vault.exists():
        return False

    if not vault.is_dir():
        raise RuntimeError(f"Vault path exists but is not a directory: {vault}")

    return any(vault.iterdir())


def bootstrap(vault, title):
    print("=== OKF Wiki Bootstrap ===")
    print(f"Installer: {INSTALLER_ROOT}")
    print(f"Vault:     {vault}")

    if is_existing_installation(vault):
        print()
        print("Existing installation detected.")
        print(f"No changes made to: {vault}")
        print()
        print("Use the existing-installation workflow for migration or inspection.")
        return 2

    vault.parent.mkdir(parents=True, exist_ok=True)

    print()
    print("Fresh installation detected.")

    interests = ask_list("Interests")
    contracts = ask_list("Contracts")
    gates = ask_list("Gates")

    print()
    print("=== Initialize vault ===")
    run([
        sys.executable,
        str(SCRIPT_DIR / "okf_init.py"),
        str(vault),
        "--title",
        title,
    ])

    print()
    print("=== Install local agent instructions ===")
    install_agents(vault)

    print()
    print("=== Create local configuration ===")
    config = save_config(vault, interests, contracts, gates)
    ensure_gitignore(vault)

    print()
    print("=== Expose local skill ===")
    expose_skill(vault)

    print()
    print("=== Validate offline core ===")

    run([
        sys.executable,
        str(SCRIPT_DIR / "okf_status.py"),
        "--vault",
        str(vault),
    ])

    run([
        sys.executable,
        str(SCRIPT_DIR / "okf_index.py"),
        "--vault",
        str(vault),
    ])

    run([
        sys.executable,
        str(SCRIPT_DIR / "okf_search.py"),
        "OKF",
        "--vault",
        str(vault),
    ])

    run([
        sys.executable,
        str(SCRIPT_DIR / "okf_lint.py"),
        "--vault",
        str(vault),
    ])


    print()
    print("=== Git checkpoint ===")
    checkpoint_created = create_git_checkpoint(vault)

    if checkpoint_created:
        print("Created bootstrap Git checkpoint.")
    else:
        print("No Git checkpoint needed.")


    print()
    print("=== Bootstrap complete ===")
    print(f"Vault:  {vault}")
    print(f"Config: {config}")
    print(f"Skill:  {vault / '.okf-wiki' / 'skill'}")
    print(f"Git:    {'checkpoint created' if checkpoint_created else 'not available or unchanged'}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a local OKF Wiki installation"
    )

    parser.add_argument(
        "vault_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_VAULT,
        help="Vault directory",
    )

    parser.add_argument(
        "--title",
        default="OKF Wiki",
        help="Wiki title",
    )

    args = parser.parse_args()

    try:
        return bootstrap(args.vault_dir.resolve(), args.title)
    except KeyboardInterrupt:
        print("\nBootstrap cancelled.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
