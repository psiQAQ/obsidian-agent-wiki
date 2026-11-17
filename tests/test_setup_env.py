"""Environment bootstrap checks without downloads or external directory writes."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from setup_env import setup_environment


class SetupEnvironmentCase(unittest.TestCase):
    def setUp(self):
        cache = REPO / ".cache/tests"
        cache.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=cache, prefix="环境 setup-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        self.lock = self.root / "uv.lock"
        self.lock.write_bytes(b"version = 1\r\n")
        self.enterContext(redirect_stdout(io.StringIO()))
        self.which = self.enterContext(patch("setup_env.shutil.which", side_effect=lambda name: f"/tools/{name}"))
        self.process = Mock(pid=123)
        self.process.wait.return_value = 0
        self.popen = self.enterContext(patch("setup_env.subprocess.Popen", return_value=self.process))

    def test_sync_uses_locked_dependencies_and_repo_local_paths(self):
        original_environment = os.environ.copy()
        setup_environment(self.root)
        command = self.popen.call_args.args[0]
        options = self.popen.call_args.kwargs
        self.assertEqual(command, ["/tools/uv", "sync", "--locked", "--dev", "--python", "3.14"])
        self.assertEqual(options["cwd"], self.root)
        for name in ("TEMP", "TMP", "TMPDIR", "UV_CACHE_DIR", "UV_PROJECT_ENVIRONMENT"):
            self.assertTrue(Path(options["env"][name]).is_relative_to(self.root))
        self.assertEqual(options["env"]["UV_PYTHON_DOWNLOADS"], "automatic")
        self.assertTrue((self.root / ".cache/tmp").is_dir())
        self.assertEqual(os.environ, original_environment)
        self.assertEqual(self.lock.read_bytes(), b"version = 1\r\n")

    def test_uv_selects_python_314_independently_of_bootstrap_interpreter(self):
        with patch("setup_env.sys.version_info", (3, 13, 0)), patch("setup_env.sys.executable", "/tools/python3.13"):
            setup_environment(self.root)
        command = self.popen.call_args.args[0]
        self.assertEqual(command[command.index("--python") + 1], "3.14")
        self.assertNotIn("/tools/python3.13", command)

    def test_sync_allows_missing_interpreter_download_even_if_parent_disables_it(self):
        with patch.dict(os.environ, {"UV_PYTHON_DOWNLOADS": "never"}):
            setup_environment(self.root)
            self.assertEqual(self.popen.call_args.kwargs["env"]["UV_PYTHON_DOWNLOADS"], "automatic")
            self.assertEqual(os.environ["UV_PYTHON_DOWNLOADS"], "never")

    def test_missing_tools_fail_without_starting_sync(self):
        for missing in ("uv", "git"):
            with self.subTest(missing=missing):
                self.which.side_effect = lambda name: None if name == missing else f"/tools/{name}"
                with self.assertRaises(RuntimeError):
                    setup_environment(self.root)
        self.popen.assert_not_called()
        self.assertFalse((self.root / ".cache").exists())

    def test_missing_project_files_fail_without_creating_cache(self):
        for name in ("pyproject.toml", "uv.lock"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(FileNotFoundError, name):
                        setup_environment(self.root)
                    self.popen.assert_not_called()
                    self.assertFalse((self.root / ".cache").exists())
                finally:
                    path.write_bytes(original)

    def test_sync_failure_is_reported_without_retry_or_lock_rewrite(self):
        self.process.wait.return_value = 1
        with self.assertRaisesRegex(RuntimeError, "uv 同步失败"):
            setup_environment(self.root)
        self.popen.assert_called_once()
        self.assertEqual(self.lock.read_bytes(), b"version = 1\r\n")


if __name__ == "__main__":
    unittest.main()
