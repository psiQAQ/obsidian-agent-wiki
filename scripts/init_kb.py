"""Copy the local template and initialize a new independent Git repository."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

from kb_common import ConfigError, KnowledgeBase, REPO_ROOT, files_under, within


def initialize(repo: Path, name: str, description: str) -> Path:
    if not name or name != name.strip() or name.endswith(".") or re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.startswith("."):
        raise ValueError("name must be a single visible Windows-safe directory name")
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name):
        raise ValueError("reserved Windows directory name")
    container = repo / "knowledge-base"
    if container.is_symlink() or container.is_junction() or not within(container, repo):
        raise ValueError("knowledge-base must be a real directory inside this repository")
    destination = container / name
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"destination already exists: {destination}")
    template = repo / "knowledge-base-template" / "llm-wiki"
    KnowledgeBase.load(template)
    for path in files_under(template):
        if path.name == ".git" or ".obsidian" in path.relative_to(template).parts:
            raise ValueError("template contains repository or Obsidian metadata")
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git is required; install it explicitly before initialization")
    container.mkdir(exist_ok=True)
    shutil.copytree(template, destination, ignore=shutil.ignore_patterns(".git", ".obsidian", ".cache", ".venv", "__pycache__"))
    readme = destination / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("{{kb_name}}", name).replace("{{description}}", description)
    readme.write_text(text, encoding="utf-8", newline="\n")
    result = subprocess.run([git, "init", "--initial-branch=main", str(destination)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"Git initialization failed; newly copied files remain at {destination}: {result.stderr.strip()}")
    return destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="a new directory name under knowledge-base/")
    parser.add_argument("--description", required=True, help="knowledge-base introduction for README")
    args = parser.parse_args(argv)
    try:
        target = initialize(REPO_ROOT, args.name, args.description)
    except (OSError, ValueError, ConfigError, RuntimeError) as error:
        print(f"Initialization failed: {error}", file=sys.stderr)
        return 2
    print(f"Created: {target}\nLocal Git initialized; no remote or commit was created.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
