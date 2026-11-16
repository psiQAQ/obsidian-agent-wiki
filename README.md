# Obsidian 与 Agent 共享知识库

在 Obsidian 中阅读、写笔记，把需要积累的资料交给 Agent 整理成有来源、能持续更新的知识页。不同研究方向分别放进独立知识库，共用一套 Obsidian 配置，各自保存本地 Git 历史。

第一次使用，按下面的“开始使用”完成一份资料的摄入。已经有知识库，可以直接打开该库的 README，或先看[知识库使用手册](knowledge-base-template/llm-wiki/README.md)中的任务示例。

## 仓库结构

```text
obsidian/                              # 整个 Obsidian Vault；本机位于 D:\obsidian
├─ README.md                           # 整个仓库的使用入口
├─ AGENTS.md                           # Agent 的共享环境、授权与多库规则
├─ knowledge-base/                     # 真正使用的知识库；根 Git 不收录这里的内容
│  └─ <库名>/                          # 一个独立方向，含自己的 README、资料和本地 Git
├─ knowledge-base-template/             # 创建知识库时使用的模板与参考
│  ├─ llm-wiki/                        # 本仓库维护的融合模板；不要在这里存个人资料
│  └─ kepano-obsidian/                 # Steph Ango 上游参考子模块，保留其原有内容
├─ .obsidian/                          # 所有知识库共用的 Obsidian 设置、插件和主题
├─ .agents/skills/                     # Agent 可读取的知识库与 Obsidian 操作技能
├─ scripts/                            # 初始化知识库、只读检查资料和链接的工具
├─ tests/                              # 工具的验证用例，使用隔离测试材料
├─ docs/                               # 设计依据、来源材料和方案选择记录
├─ pyproject.toml、uv.lock              # 共享 Python 工具的依赖声明与锁定版本
├─ .venv/                              # 本机 Python 环境，环境准备后生成，不纳入 Git
├─ .cache/                             # 本机缓存和验证中间文件，不纳入 Git
└─ .git/                               # 根仓库的本地版本历史
```

一个 **Vault** 是 Obsidian 打开的整棵文件夹；一个 **知识库** 是其中 `knowledge-base/<库名>/` 下的内容。独立使用 Git 不会让子知识库自动变成另一个 Vault。当前 Vault 名称为 `obsidian`，磁盘位置是 `D:\obsidian`。

## 开始使用

### 打开共享 Vault

在 Obsidian 的仓库管理界面选择“打开本地仓库”，选中 `D:\obsidian`。打开后应看到 `knowledge-base/` 和 `knowledge-base-template/`。如果已打开这个 Vault，无需再创建一个。

日常资料放在 `knowledge-base/<库名>/`。`knowledge-base-template/llm-wiki/` 用于创建新库；直接把剪藏或私人笔记放进模板，会让它们随初始化一起复制到以后创建的库。

### 新建知识库

可以把这段话交给以本仓库为工作目录的 Agent，并替换库名和简介：

```text
请在 knowledge-base/ 下新建“研究示例”知识库，简介为“积累研究资料与个人思考”。
使用融合模板，先确认模板内没有夹带个人资料，保留现有知识库。
创建后检查结构，并给我 README 和知识索引的入口。
```

创建成功后会得到 `knowledge-base/研究示例/`，其中包含 README、AGENTS、原始资料目录、人工笔记目录、知识索引和独立本地 Git。新库不会自动上传，也不会自动摄入已有资料。

需要自己运行命令时，先完成[环境](#环境)准备，然后在根目录 PowerShell 执行：

```powershell
Set-Location -LiteralPath 'D:\obsidian'
uv run --no-sync python scripts/init_kb.py '研究示例' --description '积累研究资料与个人思考。'
uv run --no-sync python scripts/check_kb.py 'knowledge-base/研究示例'
```

初始化只接受新目录名，已有同名目录会被拒绝；换一个名字或直接使用已有库，不要覆盖。脚本会复制整个融合模板，因此运行前也须确认模板中没有个人资料。若环境缺失，按“环境”一节处理；已有库缺少配置时，请 Agent 先评估，不在原位置重复初始化。

### 放入第一份资料

以新建的“研究示例”为例，把一份外部文章 `示例文章.md` 及其必要附件放入该库的 `raw/`，然后告诉 Agent：

```text
目标是 knowledge-base/研究示例。
请阅读 raw/示例文章.md，先与我讨论主要内容、哪些部分值得写进知识库，
以及已有知识中哪些页面可能需要更新。
```

讨论后，再说“按刚才讨论的范围摄入这份资料”。Agent 会保留原件，根据新增知识生成或更新 wiki 页面，并更新索引和操作日志。如果资料没有新增内容，只记录处理结果，不强行生成摘要。

用 PDF、扫描件、网页或自己的笔记开始时，参照[知识库手册的各类示例](knowledge-base-template/llm-wiki/README.md#按目的使用知识库)。单份资料先讨论；需要连续处理多份时，明确说“批量摄入”并指定范围。

### 查看结果并继续使用

打开新库的 `wiki/index.md` 看页面摘要，打开 `wiki/overview.md` 看逐步形成的综述，打开 `knowledge.base` 按属性浏览。`wiki/log.md` 记录处理了哪些资料，批量处理和体检报告放在 `reports/`。

此后可以直接问“根据这个知识库，我对某个问题有哪些认识？”普通提问只回答；想留下可持续更新的内容时说“保存为分析页”，想保留当时答案时说“归档为历史快照”。阅读过程中仍可以随时打开来源核对。

## 资料应该放在哪里

下表中的路径均以一个知识库为起点，例如 `knowledge-base/研究示例/`。

| 你手里的内容 | 放置位置 | 接下来怎么做 |
| --- | --- | --- |
| 网页剪藏 | `Clippings/` | 保存后指定文件，让 Agent 摄入。 |
| PDF、扫描件、图片、外部 Markdown 或文本 | `raw/` | 保留原件；需要时提取文字或识别，再编译知识。 |
| 自己的想法、读书记录、复盘 | `Notes/` | 继续自由写作；明确要求摄入时才保存来源快照。 |
| Agent 整理后的知识、分析和分类入口 | `wiki/` | 从索引或 Bases 阅读，让 Agent 按来源维护。 |
| 图片等附件 | 所属资料或笔记旁的 `assets/` | 与所属知识库一起保留，避免放在 Vault 顶层。 |
| 批量处理、体检结果 | `reports/` | 查看未解决事项，并从日志进入对应报告。 |

原始资料摄入后保留原位。各库可约定不同目录，实际位置以该库 README 和 `kb.toml` 为准；`Notes/` 统一保留。模板目录只放模板，不能充当个人收件箱。

## 网页剪藏的 Vault 与路径

Web Clipper 的 **Vault 名称**填 `obsidian`；**Folder / Note location** 填 Vault 内相对目录，例如 `knowledge-base/研究示例/Clippings`。不要把 `D:\obsidian` 或子知识库名称填进 Vault 字段。

扩展需要单独配置，不会自动沿用本仓库的页面模板。完整设置、本机 `knowledge-base-1` 路径对照和 `vault not found` 排错，见[使用 Obsidian Web Clipper](knowledge-base-template/llm-wiki/README.md#使用%20Obsidian%20Web%20Clipper)。

## 环境

使用 Obsidian 阅读和手写笔记不需要 Python。运行本仓库的初始化与检查脚本，需要 Git、uv 和 Python 3.14；本机已建立的 `.venv` 可以直接复用，不必每次安装。

以下仅用于首次准备或确需恢复环境，由操作者明确决定安装依赖后运行。PowerShell 的工作目录为本仓库根目录：

```powershell
Set-Location -LiteralPath 'D:\obsidian'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
$env:TEMP = Join-Path (Get-Location) '.cache/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
uv sync --locked --python 3.14 --no-python-downloads
```

环境变量只影响当前终端，缓存和临时文件留在仓库内。此命令不下载 Python；本机没有 Python 3.14 时会失败，需要先明确解决解释器安装。日常使用 `uv run --no-sync`；缺依赖时先处理环境，不靠重复重试或临时下载绕过。

### 不用初始化脚本时

也可以人工复制模板。先确认融合模板只含模板文件，下面命令拒绝已有同名目标。仍在根目录 PowerShell 中执行：

```powershell
$kbTarget = Join-Path (Get-Location) 'knowledge-base/研究示例'
if (Test-Path -LiteralPath $kbTarget) { throw '目标目录已经存在，请换一个新名称。' }
New-Item -ItemType Directory -Force -Path '.\knowledge-base' | Out-Null
Copy-Item -LiteralPath '.\knowledge-base-template\llm-wiki' -Destination $kbTarget -Recurse
```

打开新库 README，将所有 `{{kb_name}}` 替换为实际库名、`{{description}}` 替换为简介，再运行：

```powershell
git -C $kbTarget init --initial-branch=main
uv run --no-sync python scripts/check_kb.py 'knowledge-base/研究示例'
```

不要从其他已使用的知识库复制 `.git` 或 `.obsidian`。检查内容后可以请 Agent 在该库创建初始本地提交；初始化本身不创建提交。

## 检查、维护与详细规则

| 想做的事 | 从哪里开始 |
| --- | --- |
| 检查并整理一个知识库 | [体检使用示例](knowledge-base-template/llm-wiki/README.md#检查并整理知识库) |
| 理解检查结果与证据限制 | [知识库规则：检查与交付](knowledge-base-template/llm-wiki/AGENTS.md#检查与交付) |
| 调整目录、分类入口或专用 Bases | [知识库规则：分类入口与 Bases](knowledge-base-template/llm-wiki/AGENTS.md#分类入口与%20Bases) |
| 更新 Steph 上游参考 | [共享规则：模板与上游维护](AGENTS.md#模板与上游维护) |
| 了解本地 Git 与公开范围 | [共享规则：Git 与公开边界](AGENTS.md#Git%20与公开边界) |
| 查看方案为什么这样设计 | [方案选择记录](docs/karpathy-llm-wiki-skill-redesign-material/redesign-choice.md) |

README 说明怎样使用；AGENTS 记录 Agent 必须遵守的步骤、字段和维护边界，用户也可以打开核对。更新公共模板不会自动改写已建立的知识库，更新上游参考也不会自动合入融合模板。
