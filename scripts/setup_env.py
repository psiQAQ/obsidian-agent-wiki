"""由 uv 选择 Python 3.14，在仓库内配置锁定的开发环境（缺少解释器时允许下载）。"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent


def setup_environment(root: Path) -> None:
    root = root.resolve()
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("未找到 uv；请先安装 uv 并将其加入 PATH。")
    if shutil.which("git") is None:
        raise RuntimeError("未找到 Git；请先安装 Git 并将其加入 PATH。")
    for name in ("pyproject.toml", "uv.lock"):
        if not (root / name).is_file():
            raise FileNotFoundError(f"仓库缺少 {name}，无法按锁文件配置环境。")

    cache = root / ".cache/uv"
    temporary = root / ".cache/tmp"
    cache.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        UV_CACHE_DIR=str(cache),
        UV_PROJECT_ENVIRONMENT=str(root / ".venv"),
        UV_PYTHON_DOWNLOADS="automatic",
        TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary),
    )
    process = subprocess.Popen(
        [uv, "sync", "--locked", "--dev", "--python", "3.14"],
        cwd=root, env=env,
    )
    print(f"uv sync PID: {process.pid}", flush=True)
    if process.wait() != 0:
        raise RuntimeError("uv 同步失败；请检查上方解释器下载或依赖同步错误。未改写锁文件。")
    print("环境准备完成：.venv；缓存和临时文件位于 .cache/。")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        setup_environment(REPO_ROOT)
    except (OSError, RuntimeError) as error:
        print(f"环境准备失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
