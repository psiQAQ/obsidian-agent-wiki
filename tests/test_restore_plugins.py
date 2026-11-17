"""Plugin recovery checks with local fixtures; never install real plugins."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from restore_plugins import main, resolve_cli, restore_plugins, run_cli


class RestorePluginsCase(unittest.TestCase):
    def setUp(self):
        cache = REPO / ".cache/tests"
        cache.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=cache, prefix="plugins-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.plugin = self.root / ".obsidian/plugins/missing-plugin"
        self.plugin.mkdir(parents=True)
        self.config = self.plugin / "data.json"
        self.original = '{\r\n  "label": "中文设置"\r\n}'.encode()
        self.config.write_bytes(self.original)
        self.selection = self.root / ".obsidian/community-plugins.json"
        self.selection.write_text('["missing-plugin", "existing-plugin"]', encoding="utf-8")
        self.existing = self.root / ".obsidian/plugins/existing-plugin"
        self.existing.mkdir()
        (self.existing / "manifest.json").write_text("{}", encoding="utf-8")
        (self.existing / "main.js").write_text("", encoding="utf-8")
        self.enterContext(redirect_stdout(io.StringIO()))

    def fake_cli(self, cli, vault, root, command, *args):
        if command == "vault":
            return str(self.root)
        if command == "plugin:install":
            self.config.write_bytes(b'{"defaults":true}')
            (self.plugin / "manifest.json").write_text("{}", encoding="utf-8")
            (self.plugin / "main.js").write_text("", encoding="utf-8")
        if command == "plugin:enable":
            self.assertEqual(self.config.read_bytes(), self.original)
        if command == "plugin":
            return "version\t9.0.0\nenabled\ttrue"
        return ""

    def test_install_restores_exact_config_before_enabling_and_skips_existing(self):
        with patch("restore_plugins.run_cli", side_effect=self.fake_cli) as call:
            restore_plugins(self.root, "中文 Vault", "cli path")
        self.assertEqual(self.config.read_bytes(), self.original)
        installs = [c.args[4] for c in call.call_args_list if c.args[3] == "plugin:install"]
        self.assertEqual(installs, ["id=missing-plugin"])
        self.assertEqual((self.existing / "manifest.json").read_bytes(), b"{}")

    def test_install_failure_and_incomplete_files_restore_config_without_enabling(self):
        for fails in (True, False):
            with self.subTest(cli_error=fails):
                def fail(cli, vault, root, command, *args):
                    if command == "vault":
                        return str(self.root)
                    self.config.unlink()
                    if fails:
                        raise RuntimeError("installation failed")
                    return "Installed"
                with patch("restore_plugins.run_cli", side_effect=fail) as call:
                    with self.assertRaises(RuntimeError):
                        restore_plugins(self.root, "vault", "cli")
                self.assertEqual(self.config.read_bytes(), self.original)
                self.assertFalse(any(c.args[3] == "plugin:enable" for c in call.call_args_list))

    def test_enable_failure_stops_without_installing_next_plugin(self):
        self.selection.write_text('["missing-plugin", "next-plugin"]', encoding="utf-8")
        def fail_enable(*args):
            if args[3] == "plugin":
                return "enabled\tfalse"
            return self.fake_cli(*args)
        with patch("restore_plugins.run_cli", side_effect=fail_enable) as call:
            with self.assertRaisesRegex(RuntimeError, "未确认插件已启用"):
                restore_plugins(self.root, "vault", "cli")
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertFalse(any("id=next-plugin" in c.args for c in call.call_args_list))

    def test_wrong_vault_stops_before_install(self):
        with patch("restore_plugins.run_cli", return_value=str(self.root / "other")) as call:
            with self.assertRaisesRegex(RuntimeError, "Vault 路径"):
                restore_plugins(self.root, "vault", "cli")
        call.assert_called_once()
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_dry_run_does_not_call_cli_or_modify_files(self):
        with patch("restore_plugins.run_cli") as call, patch("restore_plugins.resolve_cli") as resolve:
            restore_plugins(self.root, "vault", dry_run=True)
        call.assert_not_called()
        resolve.assert_not_called()
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertFalse((self.plugin / "manifest.json").exists())

    def test_invalid_selection_rejected_before_cli(self):
        for value in ({"plugin": True}, ["../outside"], [None]):
            with self.subTest(value=value):
                self.selection.write_text(json.dumps(value), encoding="utf-8")
                with patch("restore_plugins.run_cli") as call:
                    with self.assertRaises(ValueError):
                        restore_plugins(self.root, "vault", "cli")
                call.assert_not_called()

    def test_each_partial_install_is_previewed_and_repaired(self):
        for present, missing in (("manifest.json", "main.js"), ("main.js", "manifest.json")):
            with self.subTest(present=present):
                for name in ("manifest.json", "main.js"):
                    (self.plugin / name).unlink(missing_ok=True)
                (self.plugin / present).write_text("partial", encoding="utf-8")
                output = io.StringIO()
                with patch("restore_plugins.run_cli") as call, redirect_stdout(output):
                    restore_plugins(self.root, "vault", "cli", dry_run=True)
                call.assert_not_called()
                self.assertIn("待补装：missing-plugin", output.getvalue())
                self.assertIn("缺失文件：" + missing, output.getvalue())
                self.assertFalse((self.plugin / missing).exists())
                with patch("restore_plugins.run_cli", side_effect=self.fake_cli) as call:
                    restore_plugins(self.root, "vault", "cli")
                self.assertEqual(sum(c.args[3] == "plugin:install" for c in call.call_args_list), 1)
                self.assertEqual(self.config.read_bytes(), self.original)

    def test_failed_partial_install_can_be_retried(self):
        self.selection.write_text('["missing-plugin", "next-plugin"]', encoding="utf-8")
        def interrupted(cli, vault, root, command, *args):
            if command == "vault":
                return str(self.root)
            (self.plugin / "manifest.json").write_text("{}", encoding="utf-8")
            self.config.write_bytes(b"overwritten during installation")
            raise RuntimeError("interrupted installation")
        with patch("restore_plugins.run_cli", side_effect=interrupted) as call:
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                restore_plugins(self.root, "vault", "cli")
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertFalse(any("id=next-plugin" in c.args for c in call.call_args_list))
        self.selection.write_text('["missing-plugin", "existing-plugin"]', encoding="utf-8")
        with patch("restore_plugins.run_cli", side_effect=self.fake_cli) as call:
            restore_plugins(self.root, "vault", "cli")
        self.assertTrue(any(c.args[3] == "plugin:install" for c in call.call_args_list))
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_explicit_cli_takes_priority_on_every_platform(self):
        for platform in ("win32", "darwin", "linux"):
            with self.subTest(platform=platform), patch("restore_plugins.sys.platform", platform):
                with patch("restore_plugins.shutil.which") as which:
                    self.assertEqual(resolve_cli("custom CLI path"), "custom CLI path")
                which.assert_not_called()

    def test_non_windows_default_is_unchanged(self):
        for platform in ("darwin", "linux"):
            with self.subTest(platform=platform), patch("restore_plugins.sys.platform", platform):
                with patch("restore_plugins.shutil.which") as which:
                    self.assertEqual(resolve_cli(), "obsidian")
                which.assert_not_called()

    def test_windows_prefers_console_on_path(self):
        console = self.root / "中文 installation path/Obsidian.com"
        console.parent.mkdir()
        console.write_bytes(b"")
        with patch("restore_plugins.sys.platform", "win32"), patch(
            "restore_plugins.shutil.which", return_value=str(console),
        ) as which:
            self.assertEqual(resolve_cli(), str(console))
        which.assert_called_once_with("Obsidian.com")

    def test_windows_finds_console_beside_executable(self):
        console = self.root / "custom install/Obsidian.com"
        console.parent.mkdir()
        console.write_bytes(b"")
        executable = console.with_suffix(".exe")
        executable.write_bytes(b"")
        with patch("restore_plugins.sys.platform", "win32"), patch.dict(
            "restore_plugins.os.environ", {}, clear=True,
        ), patch(
            "restore_plugins.shutil.which",
            side_effect=lambda name: str(executable) if name == "Obsidian.exe" else None,
        ):
            self.assertEqual(resolve_cli(), str(console))

    def test_windows_finds_console_in_common_install_directories(self):
        for variable, relative in (
            ("LOCALAPPDATA", "Programs/Obsidian/Obsidian.com"),
            ("ProgramFiles", "Obsidian/Obsidian.com"),
            ("ProgramFiles(x86)", "Obsidian/Obsidian.com"),
        ):
            with self.subTest(variable=variable):
                base = self.root / variable
                console = base / relative
                console.parent.mkdir(parents=True)
                console.write_bytes(b"")
                with patch("restore_plugins.sys.platform", "win32"), patch.dict(
                    "restore_plugins.os.environ", {variable: str(base)}, clear=True,
                ), patch("restore_plugins.shutil.which", return_value=None):
                    self.assertEqual(resolve_cli(), str(console))

    def test_windows_does_not_fall_back_to_gui_executable(self):
        executable = self.root / "Obsidian.exe"
        executable.write_bytes(b"")
        with patch("restore_plugins.sys.platform", "win32"), patch.dict(
            "restore_plugins.os.environ", {}, clear=True,
        ), patch(
            "restore_plugins.shutil.which",
            side_effect=lambda name: str(executable) if name == "Obsidian.exe" else None,
        ):
            with self.assertRaisesRegex(RuntimeError, "未找到 Obsidian.com"):
                resolve_cli()

    def test_automatic_cli_is_used_for_every_recovery_command(self):
        with patch("restore_plugins.resolve_cli", return_value="selected console") as resolve:
            with patch("restore_plugins.run_cli", side_effect=self.fake_cli) as call:
                restore_plugins(self.root, "中文 Vault")
        resolve.assert_called_once_with(None)
        self.assertTrue(call.called)
        self.assertTrue(all(c.args[0] == "selected console" for c in call.call_args_list))

    def test_complete_plugins_skip_cli_lookup(self):
        self.selection.write_text('["existing-plugin"]', encoding="utf-8")
        with patch("restore_plugins.resolve_cli") as resolve, patch("restore_plugins.run_cli") as call:
            restore_plugins(self.root, "vault")
        resolve.assert_not_called()
        call.assert_not_called()

    def test_main_passes_default_or_explicit_cli(self):
        for argv, expected in (([], None), (["--cli", "custom CLI path"], "custom CLI path")):
            with self.subTest(argv=argv), patch("restore_plugins.REPO_ROOT", self.root):
                with patch("restore_plugins.restore_plugins") as restore:
                    self.assertEqual(main(argv), 0)
                restore.assert_called_once_with(self.root, self.root.name, expected, False)

    def test_main_reports_missing_windows_console_before_invoking_cli(self):
        error = io.StringIO()
        with patch("restore_plugins.REPO_ROOT", self.root), patch(
            "restore_plugins.sys.platform", "win32",
        ), patch.dict("restore_plugins.os.environ", {}, clear=True), patch(
            "restore_plugins.shutil.which", return_value=None,
        ), patch("restore_plugins.run_cli") as call, redirect_stderr(error):
            self.assertEqual(main([]), 2)
        call.assert_not_called()
        self.assertIn("未找到 Obsidian.com", error.getvalue())
        self.assertIn("--cli", error.getvalue())
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_cli_zero_exit_error_is_failure_and_arguments_are_separate(self):
        process = Mock(pid=123, returncode=0)
        process.communicate.return_value = ("Error: failed to install", None)
        with patch("restore_plugins.subprocess.Popen", return_value=process) as popen:
            with self.assertRaises(RuntimeError):
                run_cli("cli path", "中文 Vault", self.root, "plugin:install", "id=test")
        self.assertEqual(popen.call_args.args[0], ["cli path", "vault=中文 Vault", "plugin:install", "id=test"])


if __name__ == "__main__":
    unittest.main()
