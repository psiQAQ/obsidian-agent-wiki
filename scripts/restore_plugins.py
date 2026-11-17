"""通过官方 Obsidian CLI 安装或补装启用清单中的缺失文件，保留已有配置。"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = ("manifest.json", "main.js")


def missing_files(directory: Path) -> list[str]:
    return [name for name in REQUIRED_FILES if not (directory / name).is_file()]


def run_cli(cli: str, vault: str, root: Path, *args: str) -> str:
    process = subprocess.Popen(
        [cli, f"vault={vault}", *args], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    print(f"CLI PID {process.pid}: {' '.join(args)}", flush=True)
    output, _ = process.communicate()
    output = output.strip()
    if output:
        print(output)
    # Obsidian may report an error while still returning exit code 0.
    if process.returncode or re.search(r"\bError:", output, re.IGNORECASE):
        raise RuntimeError(f"CLI 命令失败：{args[0]}；请检查上方返回信息。")
    return output


def restore_plugins(root: Path, vault: str, cli: str, dry_run: bool = False) -> None:
    root = root.resolve()
    plugin_ids = json.loads((root / ".obsidian/community-plugins.json").read_bytes())
    if not isinstance(plugin_ids, list) or any(
        not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", item)
        for item in plugin_ids
    ):
        raise ValueError("community-plugins.json 必须是有效插件 ID 的数组。")
    pending = []
    for plugin_id in dict.fromkeys(plugin_ids):
        directory = root / ".obsidian/plugins" / plugin_id
        if not directory.resolve().is_relative_to(root):
            raise ValueError(f"插件目录指向仓库外：{plugin_id}")
        missing = missing_files(directory)
        if not missing:
            print(f"跳过已安装插件：{plugin_id}")
        else:
            action = "补装" if len(missing) < len(REQUIRED_FILES) else "安装"
            print(f"待{action}：{plugin_id}；缺失文件：{', '.join(missing)}")
            pending.append((plugin_id, directory))
    if dry_run:
        print(f"预览完成：{len(pending)} 个插件待安装或补装；未调用 CLI 或修改文件。")
        return
    if not pending:
        print("插件文件齐全，无需安装或补装。")
        return

    target = run_cli(cli, vault, root, "vault", "info=path")
    if Path(target).resolve() != root:
        raise RuntimeError("CLI 返回的 Vault 路径与本仓库不符；未安装插件。")
    for plugin_id, directory in pending:
        config = directory / "data.json"
        original = config.read_bytes() if config.exists() else None
        try:
            run_cli(cli, vault, root, "plugin:install", f"id={plugin_id}")
            missing = missing_files(directory)
            if missing:
                raise RuntimeError(f"安装文件不完整：{plugin_id}；缺失文件：{', '.join(missing)}")
        finally:
            if original is not None:
                directory.mkdir(parents=True, exist_ok=True)
                config.write_bytes(original)
        if original is not None and config.read_bytes() != original:
            raise RuntimeError(f"配置核对失败：{plugin_id}；停止启用。")
        run_cli(cli, vault, root, "plugin:enable", f"id={plugin_id}")
        info = run_cli(cli, vault, root, "plugin", f"id={plugin_id}")
        fields = dict(line.split("\t", 1) for line in info.splitlines() if "\t" in line)
        if fields.get("enabled") != "true":
            raise RuntimeError(f"未确认插件已启用：{plugin_id}；停止后续安装。")
    run_cli(cli, vault, root, "plugins:enabled", "filter=community", "versions")
    print("恢复完成。请核对以上启用列表及实际设置；启用清单写盘可能稍有延迟。")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default=REPO_ROOT.name, help="Obsidian 中的 Vault 名称")
    parser.add_argument("--cli", default="obsidian", help="官方 CLI 命令或可执行文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只列出待安装或补装项及缺失文件，不调用 CLI")
    args = parser.parse_args(argv)
    try:
        restore_plugins(REPO_ROOT, args.vault, args.cli, args.dry_run)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"恢复失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
