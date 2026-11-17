"""Root ownership reminders in isolated Git repositories; no real private data."""

from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from check_root import inspect_root, main


class RootCase(unittest.TestCase):
    def setUp(self):
        cache = REPO / ".cache/tests"
        cache.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=cache, prefix="root-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.git("init", "--initial-branch=main")
        self.put(".gitignore", (REPO / ".gitignore").read_text(encoding="utf-8"))
        self.put("README.md", "# Public\n")
        self.put("docs/old.md", "public document\n")
        self.git("add", "--", ".gitignore", "README.md", "docs/old.md")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.STDOUT)

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_unknown_root_files_and_directories_are_reviewed(self):
        names = ["新 笔记.md", "根图.excalidraw.md", "image.png", "Excalidraw/图.md", "Attachments/image.png",
                 "Daily/2026-11-17.md", "Templates/template.md", "References/book.pdf", "Categories/topic.md", "自定义目录/data.txt"]
        for name in names:
            self.put(name, "synthetic")
        self.put("docs/public.md", "public")
        self.put("README.md", "updated public")
        self.assertEqual(inspect_root(self.root), sorted(names))

    def test_ignored_paths_are_not_traversed_but_force_staged_content_warns(self):
        for name in ("assets/image.png", "Clippings/page.md", "knowledge-base/private/Notes/private.md"):
            self.put(name, "synthetic")
            self.git("check-ignore", "--", name)
        self.assertEqual(inspect_root(self.root), [])
        self.git("add", "-f", "--", "assets/image.png", "Clippings/page.md", "knowledge-base/private/Notes/private.md")
        self.assertEqual(inspect_root(self.root), ["Clippings/page.md", "assets/image.png", "knowledge-base/private/Notes/private.md"])

    def test_public_paths_are_allowed_without_expanding_from_tracked_paths(self):
        for name in (".github/workflows/test.yml", ".agents/skills/new/SKILL.md", ".obsidian/app.json", ".vscode/settings.json",
                     "knowledge-base-template/new/README.md", "scripts/new.py", "tests/test_new.py", "docs/new.md", "pyproject.toml"):
            self.put(name, "public fixture")
        self.assertEqual(inspect_root(self.root), [])
        self.put("Unexpected/tracked.txt", "old")
        self.git("add", "--", "Unexpected/tracked.txt")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
        self.put("Unexpected/tracked.txt", "changed")
        self.assertEqual(inspect_root(self.root), ["Unexpected/tracked.txt"])

    def test_staged_content_is_reviewed_even_when_worktree_file_is_deleted(self):
        self.put("Daily/note.md", "synthetic")
        self.git("add", "--", "Daily/note.md")
        (self.root / "Daily/note.md").unlink()
        self.assertEqual(inspect_root(self.root), ["Daily/note.md"])

    def test_rename_destination_is_checked_and_deletion_is_not(self):
        self.git("mv", "docs/old.md", "移动.md")
        self.assertEqual(inspect_root(self.root), ["移动.md"])
        self.git("rm", "--", "README.md")
        self.assertEqual(inspect_root(self.root), ["移动.md"])

    def test_read_only_and_exit_codes(self):
        index = self.root / ".git/index"
        before = index.read_bytes()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root)]), 0)
            self.put("人工笔记.md", "keep this")
            self.assertEqual(main(["--root", str(self.root)]), 1)
            self.assertEqual(main(["--root", str(self.root / "docs")]), 2)
            self.assertEqual(main(["--root", str(self.root / "missing")]), 2)
        self.assertEqual(index.read_bytes(), before)
        self.assertEqual((self.root / "人工笔记.md").read_text(encoding="utf-8"), "keep this")


class SharedConfigCase(unittest.TestCase):
    def test_shared_template_entry_exists_and_snapshot_properties_are_text(self):
        templates = json.loads((REPO / ".obsidian/templates.json").read_bytes())
        self.assertEqual(templates["folder"], "knowledge-base-template/llm-wiki/templates")
        self.assertTrue((REPO / templates["folder"]).is_dir())
        properties = json.loads((REPO / ".obsidian/types.json").read_bytes())["types"]
        for name in ("snapshot_source_note", "snapshot_source_mtime_ns"):
            self.assertEqual(properties[name], "text")
