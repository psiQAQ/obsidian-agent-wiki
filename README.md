# Obsidian 与 Agent 共享知识库

在 Obsidian 中阅读、写笔记，把需要积累的资料交给 Agent 整理成有来源、能持续更新的知识页。各研究方向分别放进独立知识库，共用一套 Obsidian 配置，各自保存本地 Git 历史。

第一次使用，按下面的“开始使用”完成一份资料的摄入。已经有知识库，可以直接打开该库的 README，或先看[知识库使用手册](knowledge-base-template/llm-wiki/README.md)中的任务示例。

## 环境

首次使用先安装 **uv 和 Git**，在本仓库根目录打开终端，依次运行：

```shell
# 确认 uv 和 Git 可用。
uv --version
git --version

# 安装 Python 3.14。
uv python install 3.14 --cache-dir .cache/uv

# 创建或同步共享 Python 环境。
uv run --no-project --python 3.14 --cache-dir .cache/uv python scripts/setup_env.py
```

> 本文命令均在仓库根目录运行，Windows、Ubuntu 和 macOS 使用相同命令；带空格或中文的参数使用双引号。uv 管理 Python 和根 `.venv`，缓存与临时文件放在 `.cache/`。

> 输出“环境准备完成”后即可运行后续命令。日常使用 `uv run --no-sync python ...`，依赖变化后重新准备环境；遇到下载或同步错误时，保留已有环境，按终端提示处理后重跑。

## 仓库结构

```text
obsidian/                              # 整个 Obsidian Vault；名称和磁盘位置可自定
├─ .obsidian/                          # 共享设置入库；插件和主题本体留在本机
├─ .agents/skills/                     # Agent 可读取的知识库与 Obsidian 操作技能
├─ .git/                               # 根仓库的本地版本历史
├─ .venv/                              # 共享 Python 环境，保留在本机
├─ .cache/                             # 缓存和验证中间文件，保留在本机
├─ README.md                           # 整个仓库的使用入口
├─ AGENTS.md                           # Agent 的共享环境、授权与多库规则
├─ knowledge-base/                     # 日常知识库，各库以独立本地 Git 保存内容
│  └─ <库名>/                          # 一个独立方向，含自己的 README、资料和本地 Git
├─ knowledge-base-template/             # 创建知识库时使用的模板与参考
│  ├─ llm-wiki/                        # 创建知识库的公共融合模板
│  └─ kepano-obsidian/                 # Steph Ango 上游参考子模块，保留其原有内容
├─ pyproject.toml、uv.lock              # 共享 Python 工具的依赖声明与锁定版本
├─ scripts/                            # 知识库初始化、只读检查及插件恢复工具
├─ tests/                              # 工具的验证用例，使用隔离测试材料
└─ docs/                               # 设计依据、来源材料和方案选择记录
```

一个 **Vault** 是 Obsidian 打开的整棵文件夹，里面的知识库位于 `knowledge-base/<库名>/`，各自保存 Git 历史。本文以 Vault 名称 `obsidian` 为例，实际名称以 Obsidian 中显示的名称为准。

## 开始使用

### 打开共享 Vault

在 Obsidian 的仓库管理界面选择“打开本地仓库”，选中本仓库根目录。打开后可以看到 `knowledge-base-template/`，创建知识库后会出现 `knowledge-base/`。

> 日常资料放在 `knowledge-base/<库名>/`，公共模板保存在 `knowledge-base-template/llm-wiki/`。创建前确认模板文件及正文适合复制；初始化报错时，保全原件并核对所列文件的归属。

### 新建知识库

想要创建名为“xxx研究”、描述为“积累 xxx 研究资料与个人思考。”的知识库，运行：

```shell
# 创建得到 knowledge-base/xxx研究 文件夹并初始化独立本地 Git。
uv run --no-sync python scripts/init_kb.py "xxx研究" --description "积累 xxx 研究资料与个人思考。"

# 检查知识库结构。
uv run --no-sync python scripts/check_kb.py "knowledge-base/xxx研究"
```

### 放入并整理资料

把 `示例文章.md` 及其附件放入 `knowledge-base/xxx研究/raw/`，然后告诉 Agent：

```text
请阅读 knowledge-base/xxx研究/raw/示例文章.md，
先讨论主要内容、值得积累的知识和需要更新的页面。
```

讨论后回复“按刚才讨论的范围摄入这份资料”。Agent 会保留原件，整理知识页，并更新索引和日志。

> PDF、扫描件、网页和个人笔记的操作见[知识库使用示例](knowledge-base-template/llm-wiki/README.md#按目的使用知识库)。连续处理多份资料时，指定范围并说明“批量摄入”。

### 查看结果并继续使用

在所属知识库 `xxx研究` 中查看：

| 入口 | 可以看到什么 |
| --- | --- |
| `knowledge-base/xxx研究/wiki/index.md` | 知识目录、页面链接与摘要。 |
| `knowledge-base/xxx研究/wiki/overview.md` | 逐步积累的知识综述。 |
| `knowledge-base/xxx研究/wiki/log.md` | 资料摄入、保存和维护记录。 |
| `knowledge-base/xxx研究/reports/` | 批量处理与体检报告。 |
| `knowledge-base/xxx研究/knowledge.base` | 按属性浏览知识页与历史归档。 |

向 Agent 提问可以获得带引用的回答。需要把回答留在库内时，可以选择：

- **保存为分析页**：将回答整理成可持续维护的专题文章，放在 `wiki/`，例如 `wiki/研究方法比较.md`。正文引用原始资料，并按实际关联链接已有知识页；关联页可通过反向链接找到这份分析。后续摄入和体检时可继续完善它；要把本次结论合入已有分析页，明确指定“更新 `wiki/已有分析.md`”。
- **归档为历史快照**：将当时的问题与回答保存为带日期的页面，放在 `wiki/`，例如 `wiki/研究方法比较 - YYYY-MM-DD.md`。记录归档日期，并链接当时使用的知识页。快照正文保留当时判断，所链接的知识页照常更新；维护时可提示快照可能过时。

两种操作都会更新 `wiki/index.md` 和 `wiki/log.md`。新建页面使用独立文件名，已有页面保留；详细规则见[查询、保存与归档](knowledge-base-template/llm-wiki/AGENTS.md#查询、保存与归档)。

## 资料应该放在哪里

下表中的路径均相对于所属知识库，例如 `knowledge-base/xxx研究/`。

| 内容 | 放置位置 | 后续操作 |
| --- | --- | --- |
| 网页剪藏 | `Clippings/` | 指定文件，请 Agent 摄入。 |
| PDF、扫描件、图片、外部文章 | `raw/` | 保留原件，请 Agent 提取并整理知识。 |
| 个人想法、读书记录、复盘 | `Notes/` | 自由写作，需要摄入时明确提出。 |
| Agent 整理的知识与分析 | `wiki/` | 从索引或 Bases 阅读。 |
| 附件 | 所属资料或笔记旁的 `assets/` | 随所属知识库保存。 |
| 批量处理与体检报告 | `reports/` | 查看处理结果和待办。 |

> 原始资料摄入后保留原位。实际目录以该库 README 和 `kb.toml` 为准，人工笔记统一放在 `Notes/`。

## 保存在线网页资料到本地

从[安装页面](https://obsidian.md/zh/clipper)安装 Obsidian Web Clipper，可将网页版文档、论坛帖子等保存为本地 Markdown；支持字幕提取的视频页面还可保存字幕。推荐配置和抓取练习见[Obsidian Web Clipper 配置与正文抓取](docs/Obsidian%20Web%20Clipper%20配置与正文抓取.md)。

## 恢复共享插件与主题

新检出仓库后，按以下步骤安装插件和主题。共享设置与经过审查的插件配置文件 `data.json` 由根 Git 保存，插件和主题本体保留在本地不上传 Git，从而减少插件和主题更新的影响。

> 公开插件配置文件前审查凭据、服务地址、模板路径和素材库。私密配置保留在本地，由用户确认忽略规则。

### 开启官方命令行界面功能

为了让 Agent 能直接通过命令行操作 Obsidian，需要先开启官方命令行界面功能。

仓库中的 [obsidian-cli](.agents/skills/obsidian-cli/SKILL.md) Skill 指导 Agent 读写和搜索笔记、查询属性与反向链接，以及管理插件和主题；[obsidian-markdown](.agents/skills/obsidian-markdown/SKILL.md) 和 [obsidian-bases](.agents/skills/obsidian-bases/SKILL.md) 分别提供笔记语法与总览配置规范，配合 CLI 完成内容维护。

打开当前 Vault，在 Obsidian 设置 > 关于 > 高级 中开启“命令行界面”、选择“添加到 PATH”，然后重新打开终端。详见 [Obsidian 官方 CLI 文档](https://obsidian.md/help/cli)。

```shell
# 查看官方 CLI 帮助。
obsidian help

# 确认返回当前仓库根目录。
obsidian vault "info=path"
```

> 连接异常时，确认 Obsidian 已打开，并检查 PATH 和访问权限。指定 Vault 时，将 `vault="实际 Vault 名称"` 放在命令名之前。

### 安装缺失插件并保留配置

恢复工具按 `community-plugins.json` 中的启用清单处理。先预览：

```shell
# 预览缺失或残缺的插件。
uv run --no-sync python scripts/restore_plugins.py --dry-run
```

确认待安装项并决定安装后执行：

```shell
# 安装或补装插件，保留已有配置并恢复启用状态。
uv run --no-sync python scripts/restore_plugins.py
```

> Windows 自动从 PATH 和常见安装目录查找 `Obsidian.com`；macOS、Linux 使用 PATH 中的 `obsidian`。指定官方 CLI 可追加 `--cli "完整路径"`，该参数优先于自动查找。

> 指定 Vault 可追加 `--vault "实际 Vault 名称"`。保持终端运行至结束，再核对插件启用列表和设置；报错时保留输出，处理后重跑。

> 安装脚本会自动备份已有的 `data.json`，并在插件安装或补装后自动恢复配置。详见[重装验证记录](docs/plugin-reinstall-verification.md)。

### Claudian

Claudian 提供 Obsidian 内的 Agent 对话入口，可结合笔记和选中文本进行问答、整理资料和维护笔记。

运行 `restore_plugins.py` 完成插件安装后：

1. 到 **设置 > 第三方插件 > Claudian > 供应商**，针对自己使用的 Agent 配置供应商及模型列表。
2. 到 **设置 > 第三方插件 > Claudian > 通用 > 环境 > 共享环境**，按需填写 Agent 启动时使用的环境变量，例如 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`。

> 本地配置保存在 Vault 根目录的 `.claudian/claudian-settings.json`；`.claudian/` 已被根 `.gitignore` 默认忽略，配置和会话保留在本机。

### 安装主题

可到 设置 > 外观 > 主题 > 管理 的社区主题面板中下载自己喜欢的主题。

例如安装并启用当前配置使用的 Minimal 主题（可搭配 Minimal Theme Settings 插件进行更多配置调整）：

```shell
# 安装并启用 Minimal 主题，按需替换命令中的主题名称。
obsidian theme:install "name=Minimal"
obsidian theme:set "name=Minimal"

# 查看当前主题。
obsidian theme
```

## 检查、维护与详细规则

这一节是维护仓库和知识库时的自查与操作入口。用户可以确认哪些文件需要在提交前核对、修改工具后如何检查，以及整理知识库时该看哪份说明；Agent 则用这些检查验收改动，并按对应规则执行维护任务。

### 提交共享文件前：检查文件归属

根 Git 保存共享配置、工具和公共模板。下面的只读检查会列出公共路径白名单外的变更，帮助用户或 Agent 发现可能放错位置的文件，在提交前确认其用途和归属：

```shell
# 检查根仓库的变更路径。
uv run --no-sync python scripts/check_root.py
```

> 检查范围为 Git 可见的变更路径，白名单位于 `scripts/check_root.py`。白名单外的路径标记为 `REVIEW`，需人工确认归属；内容和隐私另行审查。退出码：`0` 检查范围内通过，`1` 有待确认项，`2` 配置或运行失败。

> 本地评审材料放在 `docs/LLM-review/`，保存前核对本地 Git 忽略配置；正式验收记录放在 `docs/` 下可跟踪的位置。

### 修改脚本后：检查功能是否受影响

修改 `scripts/` 中的工具后，用自动化测试检查已有功能是否仍符合预期。Agent 应先选择与本次改动相关的测试；需要完整回归时，使用下面的命令运行全部测试：

```shell
# 使用隔离材料运行测试，缓存保存在 .cache/。
uv run --no-sync python -m pytest
```

> [GitHub Actions](https://github.com/psiQAQ/obsidian-agent-wiki/actions/workflows/python-tests.yml) 在 Windows、Ubuntu 和 macOS 上执行环境准备、测试和脚本帮助检查。Obsidian 桌面界面与真实插件安装另行验收。

### 整理或调整知识库时：查阅对应说明

下表是按任务查阅的入口：用户可通过使用示例明确操作步骤，Agent 则按对应规则确认处理范围、保护原始资料并说明检查结果。

| 想做的事 | 从哪里开始 |
| --- | --- |
| 检查并整理一个知识库 | [体检使用示例](knowledge-base-template/llm-wiki/README.md#检查并整理知识库) |
| 理解检查结果与证据限制 | [知识库规则：检查与交付](knowledge-base-template/llm-wiki/AGENTS.md#检查与交付) |
| 调整目录、分类入口或专用 Bases | [知识库规则：分类入口与 Bases](knowledge-base-template/llm-wiki/AGENTS.md#分类入口与%20Bases) |
| 更新 Steph 上游参考 | [共享规则：模板与上游维护](AGENTS.md#模板与上游维护) |
| 了解本地 Git 与公开范围 | [共享规则：Git 与公开边界](AGENTS.md#Git%20与公开边界) |
| 查看方案为什么这样设计 | [方案选择记录](docs/karpathy-llm-wiki-skill-redesign-material/redesign-choice.md) |

README 提供使用步骤，AGENTS 记录 Agent 的操作规则。

> 页面模板用法见[页面模板说明](knowledge-base-template/llm-wiki/README.md#页面模板的三种用法)。已有库升级、改名或调整目录，按[绑定与升级顺序](knowledge-base-template/llm-wiki/AGENTS.md#分类入口与%20Bases)评估，并保全人工内容；上游参考适配与独立 Vault 迁出另行规划。
