"""Read-only ownership reminders for Git-visible changes in the shared Vault root."""

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
# Explicit public paths at aa40d81; never infer permission from the current index.
PUBLIC_DIRECTORIES = {".agents", ".github", ".obsidian", ".vscode", "docs", "knowledge-base-template", "scripts", "tests"}
PUBLIC_ROOT_FILES = {".gitignore", ".gitmodules", ".python-version", "AGENTS.md", "README.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml", "skills-lock.json", "uv.lock"}


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout.decode("utf-8", errors="surrogateescape")


def inspect_root(root: Path) -> list[str]:
    root = root.resolve(strict=True)
    top = Path(git_output(root, "rev-parse", "--show-toplevel").strip()).resolve()
    if top != root:
        raise ValueError("root must be the Git repository root, not a nested directory")
    # Git honors ignores; no file bodies, private libraries or ignored trees read.
    records = iter(git_output(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=all").split("\0"))
    findings = set()
    for record in records:
        if not record:
            continue
        status, name = record[:2], record[3:]
        if "R" in status or "C" in status:
            next(records)  # -z puts the destination first, then the original path.
        if status in {" D", "D "}:
            continue
        path = PurePosixPath(name)
        public = (name in PUBLIC_ROOT_FILES if len(path.parts) == 1
                  else path.parts[0] in PUBLIC_DIRECTORIES)
        if not public:
            findings.add(name)
    return sorted(findings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="shared Git root; defaults to this script's repository")
    args = parser.parse_args(argv)
    try:
        findings = inspect_root(args.root)
    except (OSError, ValueError, RuntimeError, StopIteration) as error:
        print(f"Root check failed: {error}", file=sys.stderr)
        return 2
    for path in findings:
        print(f"[REVIEW] root-content-owner | {path} | confirm destination/ownership before committing; content was not read")
    print(f"Summary: {len(findings)} review item(s). Read-only; no content was classified, moved or staged.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
