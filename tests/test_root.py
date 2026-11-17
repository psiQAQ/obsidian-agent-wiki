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

    def test_new_root_note_and_content_directories_are_reviewed(self):
        names = ["新 笔记.md", "根图.excalidraw.md", "Excalidraw/图.md", "Attachments/image.png"]
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
        self.git("add", "-f", "--", "assets/image.png", "Clippings/page.md")
        self.assertEqual(inspect_root(self.root), ["Clippings/page.md", "assets/image.png"])

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
