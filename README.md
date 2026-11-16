# Obsidian 与 Agent 共享知识库模板

用一个 Obsidian Vault 共用配置，用多个本地 Git 仓库分别管理独立方向的知识库。Agent 负责资料编译和知识维护，人工笔记保留自己的观点和写作过程。

## 布局与入口

- `knowledge-base/`：各独立知识库，仅留本地，根 Git 忽略整个目录。
- [融合初始模板](knowledge-base-template/llm-wiki/README.md)：简约目录、页面模板、索引和 Bases。
- [Steph 上游参考](knowledge-base-template/kepano-obsidian/Readme.md)：子模块，内容保持上游；融合模板单独维护。
- [Agent 规则](AGENTS.md) 与 [逐项选择记录](docs/karpathy-llm-wiki-skill-redesign-material/redesign-choice.md)：维护边界及四方方案的选择依据。

将本仓库根目录作为 Obsidian Vault 打开。共享配置已启用 Bases 与 Templates；页面模板入口指向融合模板，附件使用当前笔记旁的 `assets/`。从目标库的 `Notes/` 文件夹新建人工笔记，并插入“人工笔记模板”。一般的新建快捷键沿用用户设置，不会自动识别应进入哪个知识库；错放内容可在明确归属后请 Agent 整理。

## 环境

前提：已安装 Git、uv 和 Python 3.14。以下命令使用 PowerShell，工作目录为本仓库根目录。依赖安装属于环境搭建步骤，须已获得操作者授权。

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
$env:TEMP = Join-Path (Get-Location) '.cache/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
uv sync --locked --python 3.14 --no-python-downloads
```

这些环境变量只用于当前终端会话；临时目录和 uv 缓存留在仓库内。已具备 Python 3.14 时不重复下载安装解释器。

## 新建知识库

在仓库根目录运行：

```powershell
uv run --no-sync python scripts/init_kb.py '示例知识库' --description '这个知识库用于积累某个独立方向的资料与思考。'
uv run --no-sync python scripts/check_kb.py 'knowledge-base/示例知识库'
```

初始化只接受一个新目录名，不覆盖已有内容，完成后新库有自己的 `.git`。脚本不设置远端、不自动上传；在检查内容后于该库提交初始版本。检查退出码：`0` 无发现，`1` 有确定错误或待核实事项，`2` 配置或运行失败。即便为 `0`，也不表示已经逐条证明所有事实。

也可以人工复制整个融合模板到 `knowledge-base/`，修改文件夹名以及 README 标题、简介，然后在新库运行 `git init`。不需要复制或配置一套 `.obsidian`。各库按 `kb.toml` 自定布局，人工笔记目录统一为 `Notes/`。

## 日常使用

网页剪藏使用各库独立的 `Clippings/`，其他原始资料使用 `raw/`；二者都保留原件、不在摄入后移动。使用 Obsidian Web Clipper 时选择共享根 Vault，将保存位置设为 `knowledge-base/<库名>/Clippings`。浏览器扩展需单独配置，操作步骤见[融合模板的 Web Clipper 说明](knowledge-base-template/llm-wiki/README.md#使用-obsidian-web-clipper)。

指定目标库后交给 Agent 摄入资料。指定单份先讨论；明确批量时逐份串行处理。资料保留原位，有新增内容才建摘要。普通查询只回答；“保存”生成持续维护的分析，“归档”保存历史快照。

生成页用 `managed_by: agent` 标记，正文通过相对链接引用来源；`sources` 是从当前文件出发的相对路径列表。分类关系的双链写清从 Vault 根起的路径。全库属性类型共享，勿在不同库中把同名属性设成不同类型。

索引服务于阅读和 Agent 检索；Bases 提供生成知识、人工笔记和类别视图。打开每库根目录的 `knowledge.base`，或在该库内嵌入该视图。它按当前上下文所属的 `knowledge-base/<库名>/` 限定范围，处于公共模板、根目录或其他不明上下文时不展示私有内容。视图不表示允许 Agent 跨库读取。

体检可以按原文修复生成知识，但机器只检查结构和可机械定位的证据线索。真正的事实核对、推断判断和来源分歧仍需要 Agent 阅读原文。PDF、图片等未解析材料会报告为需要人工核查，不自动安装 OCR 依赖。

证据线索检查只定位部分数字写法、ISO 日期和较长的直接引语；普通短整数、改写后的引语、定性陈述及计算推导仍须阅读核实。字符串匹配成功也不证明上下文或结论成立。

## 更新 Steph 参考子模块

以下为有意更新上游时的手动流程，先确认子模块无本地改动；它不会同步改写融合模板或现有知识库。

```powershell
git -C knowledge-base-template/kepano-obsidian status --short
git submodule update --init -- knowledge-base-template/kepano-obsidian
git -C knowledge-base-template/kepano-obsidian fetch origin main
git -C knowledge-base-template/kepano-obsidian log --oneline HEAD..origin/main
git -C knowledge-base-template/kepano-obsidian diff --stat HEAD origin/main
```

查看差异并决定更新后再执行：

```powershell
git -C knowledge-base-template/kepano-obsidian switch --detach origin/main
git add -- knowledge-base-template/kepano-obsidian
git commit -m 'chore: 更新 Steph 上游参考模板'
```

如有本地改动，先处理其归属，不强制切换或覆盖。父仓库记录确定提交，其他检出通过 `git submodule update --init` 复现该版本。融合模板需要吸收的改动另行审查和实施。

## 验证与发布边界

在根目录运行 `uv run --no-sync python -m unittest discover -s tests -v`。测试目录在仓库内部，测试不能操作现有知识库。实际 Obsidian 中还应检查 Bases、属性、相对链接及附件位置，静态检查不能替代实际渲染。

根仓库可作为公开模板发布，发布前检查本次变更和待发布文件：不带 `knowledge-base/`、运行缓存、工作区、书签、图谱状态、私密插件配置或缺少发布许可的参考材料。现有用户插件和主题改动不自动属于本项目交付。本文不授权设置 remote、push 或创建 GitHub 仓库。
