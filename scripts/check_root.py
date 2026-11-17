"""Read-only ownership reminders for Git-visible changes in the shared Vault root."""

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_FOLDERS = {"Excalidraw", "Attachments", "assets", "Clippings"}


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
        if "D" in status:
            continue
        path = PurePosixPath(name)
        new_root_note = len(path.parts) == 1 and path.suffix.lower() == ".md" and (status == "??" or any(code in status for code in "ARC"))
        loose_content = path.parts[0] in CONTENT_FOLDERS and len(path.parts) > 1
        if new_root_note or loose_content:
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
