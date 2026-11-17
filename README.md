# Obsidian 与 Agent 共享知识库

在 Obsidian 中阅读、写笔记，把需要积累的资料交给 Agent 整理成有来源、能持续更新的知识页。不同研究方向分别放进独立知识库，共用一套 Obsidian 配置，各自保存本地 Git 历史。

第一次使用，按下面的“开始使用”完成一份资料的摄入。已经有知识库，可以直接打开该库的 README，或先看[知识库使用手册](knowledge-base-template/llm-wiki/README.md)中的任务示例。

## 环境

首次使用先安装 **Python 3.14、uv 和 Git**，在本仓库根目录打开终端，确认 `python --version` 显示 3.14，再运行：

```shell
python scripts/setup_env.py
```

Windows、Ubuntu 和 macOS 使用相同命令。若系统把 Python 3.14 命名为 `python3` 或 `python3.14`，仅将上面的 `python` 换成该命令；后续由 uv 选择项目解释器，无需激活虚拟环境。

脚本按 `uv.lock` 创建或同步根 `.venv`，包含运行依赖和 pytest 开发依赖；缓存及临时文件放在 `.cache/`，不修改全局环境变量，也不下载 Python。输出“环境准备完成”即为成功。缺少工具、解释器版本不符或锁文件缺失时会明确失败；网络或依赖同步失败时保留错误信息，解决原因后再运行，不删除已有环境重试。

日常运行使用 `uv run --no-sync python ...`，依赖变化后才重新准备环境。仅用 Obsidian 阅读和手写笔记不需要运行脚本，但本手册后续的命令示例均以环境已准备好为前提。

除非另有说明，以下命令都在仓库根目录运行，路径相对此目录；带空格或中文的参数使用双引号。仓库可以放在任意磁盘位置，不要求固定盘符或用户名目录。

## 仓库结构

```text
obsidian/                              # 整个 Obsidian Vault；名称和磁盘位置可自定
├─ README.md                           # 整个仓库的使用入口
├─ AGENTS.md                           # Agent 的共享环境、授权与多库规则
├─ knowledge-base/                     # 真正使用的知识库；根 Git 不收录这里的内容
│  └─ <库名>/                          # 一个独立方向，含自己的 README、资料和本地 Git
├─ knowledge-base-template/             # 创建知识库时使用的模板与参考
│  ├─ llm-wiki/                        # 本仓库维护的融合模板；不要在这里存个人资料
│  └─ kepano-obsidian/                 # Steph Ango 上游参考子模块，保留其原有内容
├─ .obsidian/                          # 共享设置入库；插件和主题本体留在本机
├─ .agents/skills/                     # Agent 可读取的知识库与 Obsidian 操作技能
├─ scripts/                            # 知识库初始化、只读检查及插件恢复工具
├─ tests/                              # 工具的验证用例，使用隔离测试材料
├─ docs/                               # 设计依据、来源材料和方案选择记录
├─ pyproject.toml、uv.lock              # 共享 Python 工具的依赖声明与锁定版本
├─ .venv/                              # 本机 Python 环境，环境准备后生成，不纳入 Git
├─ .cache/                             # 本机缓存和验证中间文件，不纳入 Git
└─ .git/                               # 根仓库的本地版本历史
```

一个 **Vault** 是 Obsidian 打开的整棵文件夹；一个 **知识库** 是其中 `knowledge-base/<库名>/` 下的内容。独立使用 Git 不会让子知识库自动变成另一个 Vault。本文以 Vault 名称 `obsidian` 为例；实际名称以 Obsidian 中显示的名称为准。

## 开始使用

### 打开共享 Vault

在 Obsidian 的仓库管理界面选择“打开本地仓库”，选中本仓库根目录。打开后应看到 `knowledge-base/` 和 `knowledge-base-template/`。如果已打开这个 Vault，无需再创建一个。

日常资料放在 `knowledge-base/<库名>/`。`knowledge-base-template/llm-wiki/` 用于创建新库；直接把剪藏或私人笔记放进模板，会让它们随初始化一起复制到以后创建的库。

### 新建知识库

可以把这段话交给以本仓库为工作目录的 Agent，并替换库名和简介：

```text
请在 knowledge-base/ 下新建“研究示例”知识库，简介为“积累研究资料与个人思考”。
使用融合模板，先确认模板内没有夹带个人资料，保留现有知识库。
创建后检查结构，并给我 README 和知识索引的入口。
```

创建成功后会得到 `knowledge-base/研究示例/`，其中包含 README、AGENTS、原始资料目录、人工笔记目录、知识索引和独立本地 Git。新库不会自动上传，也不会自动摄入已有资料。

需要自己运行命令时，先完成[环境](#环境)准备，然后在根目录终端执行：

```shell
uv run --no-sync python scripts/init_kb.py "研究示例" --description "积累研究资料与个人思考。"
uv run --no-sync python scripts/check_kb.py "knowledge-base/研究示例"
```

初始化只接受新目录名，已有同名目录会被拒绝；换一个名字或直接使用已有库，不要覆盖。脚本会复制整个融合模板，因此运行前也须确认模板中没有个人资料。若环境缺失，按“环境”一节处理；已有库缺少配置时，请 Agent 先评估，不在原位置重复初始化。

脚本会按新库的 `kb.toml` 自动填写 `knowledge.base` 的库根、wiki 和 Notes 路径。总览固定绑定该库；“现行知识”和“按类别浏览”仅展示 wiki 内的生成知识，历史快照在“历史归档”视图中按归档日期倒序查看。

### 不用初始化脚本时

也可以通过文件管理器复制模板：先确认 `knowledge-base-template/llm-wiki/` 没有个人资料，将其复制到尚不存在的 `knowledge-base/研究示例/`，不要覆盖已有目录。将新库 README 中的 `{{kb_name}}` 和 `{{description}}` 分别替换为库名和简介，再按[总览绑定步骤](knowledge-base-template/llm-wiki/AGENTS.md#分类入口与%20Bases)填写新库 `knowledge.base` 的三个占位符。默认布局分别为 `__KB_ROOT__` → `knowledge-base/研究示例`、`__WIKI_PATH__` → `knowledge-base/研究示例/wiki`、`__NOTES_PATH__` → `knowledge-base/研究示例/Notes`。然后在仓库根目录运行：

```shell
git -C "knowledge-base/研究示例" init --initial-branch=main
uv run --no-sync python scripts/check_kb.py "knowledge-base/研究示例"
```

不要从其他已使用的知识库复制 `.git` 或 `.obsidian`。检查内容后可以请 Agent 在该库创建初始本地提交；初始化本身不创建提交。

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

Web Clipper 的 **Vault 名称**填 `obsidian`；**Folder / Note location** 填 Vault 内相对目录，例如 `knowledge-base/研究示例/Clippings`。Vault 字段应替换为实际 Vault 名称，不填磁盘绝对路径或子知识库名称。

扩展需要单独配置，不会自动沿用本仓库的页面模板。完整设置、示例库的相对路径对照和 `vault not found` 排错，见[使用 Obsidian Web Clipper](knowledge-base-template/llm-wiki/README.md#使用%20Obsidian%20Web%20Clipper)。

## 恢复共享插件与主题

根 Git 保存共享设置和经过审查的插件 `data.json`，忽略插件发行文件及主题本体。`manifest.json` 属于发行文件。新检出仓库需要另行安装插件和主题；已有机器上的本体仍留在磁盘。取消跟踪不改写 Git 历史，旧提交仍包含当时的发行文件。

插件 `data.json` 可能包含凭据、服务地址、模板路径或素材库。提交前必须审查；发现私密内容时暂不提交，由用户决定是否为该插件添加忽略规则。Claudian 的模型配置位于已忽略的 `.claudian/claudian-settings.json`。当前保留的 Excalidraw 配置中服务密钥为空、内嵌素材库为空，模板与素材目录仍需在实际使用时自行准备。

### 准备官方 CLI

打开当前 Vault，在 Obsidian 设置中开启“命令行界面”并选择“添加到 PATH”（本机版本位于“关于”；新版界面可能位于“常规”），重新打开终端。使用官方随应用安装的 CLI，不安装同名第三方 npm 工具。命令及平台要求见 [Obsidian 官方 CLI 文档](https://obsidian.md/help/cli)。

```shell
obsidian help
obsidian vault "info=path"
```

CLI 默认按当前工作目录定位 Vault；确认返回的是本仓库根目录。需要显式指定时，将 `vault="实际 Vault 名称"` 放在命令名之前。若找不到命令，检查 PATH 注册并重新打开终端；若无法连接，确认 Obsidian 已打开。Agent 的受限环境可能无法访问 CLI 或本地连接，应按实际权限错误处理，不反复安装软件。

### 安装缺失插件并保留配置

以下用于新检出仓库或恢复缺失插件，需操作者明确决定安装后运行。已经存在 `manifest.json` 的插件跳过，不作为升级流程。`community-plugins.json` 只包含启用的插件；其他曾安装但未启用的插件需另行指定。

批量恢复由 [restore_plugins.py](scripts/restore_plugins.py) 执行，复用前述 Python 环境，无需新增依赖。在仓库根目录先预览：

```shell
uv run --no-sync python scripts/restore_plugins.py --dry-run
```

确认待安装项后执行：

```shell
uv run --no-sync python scripts/restore_plugins.py
```

脚本默认以仓库文件夹名称定位 Vault；实际显示名称不同时，用 `--vault "实际 Vault 名称"` 指定。脚本先读取启用清单并核对 CLI 的 Vault 路径，再逐项安装缺失插件。已有 `data.json` 暂存于内存，安装成功或失败都会恢复；核对配置字节后才启用，并检查插件是否报告已启用。不要在运行中关闭终端。若官方 CLI 不在 PATH，可用 `--cli "官方 CLI 的完整路径"` 指定；Windows 使用安装目录内的 `Obsidian.com`。

成功时输出“恢复完成”；没有缺失插件时输出“没有缺失插件，无需安装”。安装或启用失败时脚本停止后续操作并返回非零退出码，保留终端中的错误输出，处理原因后再继续。CLI 返回退出码 0 时仍会检查错误文本和实际安装文件，不会自动删除配置重试。最后核对输出中的启用列表与预期清单，以及插件实际设置；启用状态写入磁盘可能稍有延迟。

重装已存在的插件时，先在已忽略的 `.cache/` 中保全原包、配置及启用清单并确认可读，再卸载；安装失败或设置不兼容时恢复这三项。**卸载不能当作保留配置的操作。** 本机 Minimal Settings `9.0.0` 的实测中，卸载删除了 `data.json`，重新安装后也未创建它；恢复原配置再启用后设置保持一致，详见[重装验证记录](docs/plugin-reinstall-verification.md)。

### 安装主题

`appearance.json` 当前选择 Minimal；主题不在插件启用清单内，需要单独安装：

```shell
obsidian theme:install "name=Minimal"
obsidian theme:set "name=Minimal"
obsidian theme
```

确认当前主题为 Minimal，并检查其设置。Obuntu 与 VSCode 2026 是可选主题，仅在需要时分别运行 `obsidian theme:install "name=Obuntu"` 或 `obsidian theme:install "name=VSCode 2026"`；不要追加 `enable`，以免改变当前主题。

当前官方 `plugin:install` 与 `theme:install` 没有版本参数，因此上述流程恢复可用的插件和主题，不保证版本与旧机器完全一致。迁移前若需要原版本回退，应另行保全已安装发行文件。

## 检查、维护与详细规则

在仓库根目录运行脚本测试：

```shell
uv run --no-sync python -m pytest
```

测试只使用隔离材料；临时目录及 pytest 缓存留在 `.cache/`，不会读取私有知识库或安装真实 Obsidian 插件。

[GitHub Actions](https://github.com/psiQAQ/obsidian-agent-wiki/actions/workflows/python-tests.yml) 在 Windows、Ubuntu、macOS 上使用 Python 3.14 执行同一环境准备流程、pytest 和脚本帮助检查。push 或 PR 修改脚本、测试、依赖、融合模板或 workflow 时触发，也支持手动运行；仅修改根使用文档不触发。各平台结果独立报告，CI 不验证 Obsidian 桌面界面或真实插件安装。

| 想做的事 | 从哪里开始 |
| --- | --- |
| 检查并整理一个知识库 | [体检使用示例](knowledge-base-template/llm-wiki/README.md#检查并整理知识库) |
| 理解检查结果与证据限制 | [知识库规则：检查与交付](knowledge-base-template/llm-wiki/AGENTS.md#检查与交付) |
| 调整目录、分类入口或专用 Bases | [知识库规则：分类入口与 Bases](knowledge-base-template/llm-wiki/AGENTS.md#分类入口与%20Bases) |
| 更新 Steph 上游参考 | [共享规则：模板与上游维护](AGENTS.md#模板与上游维护) |
| 了解本地 Git 与公开范围 | [共享规则：Git 与公开边界](AGENTS.md#Git%20与公开边界) |
| 查看方案为什么这样设计 | [方案选择记录](docs/karpathy-llm-wiki-skill-redesign-material/redesign-choice.md) |

README 说明怎样使用；AGENTS 记录 Agent 必须遵守的步骤、字段和维护边界，用户也可以打开核对。更新公共模板不会自动改写已建立的知识库，更新上游参考也不会自动合入融合模板。
