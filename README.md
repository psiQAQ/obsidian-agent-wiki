# Obsidian Agent Wiki（个人 Vault 配置与多库协同底座）

> **作者个人公开的 Obsidian 配置与 AI Agent 协同底座**：公开分享日常使用的 `.obsidian/` 共享配置、全局工作流规则（`AGENTS.md`）与第三方 Agent Skills；通过将 `knowledge-base/` 纳入忽略，实现「公共工作流公开 + 私人知识库一库一 Git 本地隔离」。

> [!NOTE]
> **与 `Knowledge Base Manager` 插件的关系说明**
> 本仓库定位为**作者自己使用 Obsidian 的公开配置仓库**，与作者开发的 [Knowledge Base Manager](https://github.com/psiQAQ/obsidian-kb-manager) 插件**并非强绑定**：
> - 如果你想新建一个普通的 Obsidian Vault 并进行多库管理、内置模板建库或单库 Git 同步，只需单独安装该插件即可，不需要依赖本仓库；
> - 本仓库只是在个人日常配置中启用了该插件（以及其他常用社区插件），并额外提供了一套跨库共享的 `AGENTS.md` 规则、`.agents/skills/` 技能集与全局属性约定，供有类似人机协同工作流需求的用户参考或复用。

---

## 目录

- [一、使用者指南（Users）](#一使用者指南users)
  - [1. 这个仓库适合谁](#1-这个仓库适合谁)
  - [2. 核心组织模型：公共配置层 × 私有知识库层](#2-核心组织模型公共配置层--私有知识库层)
  - [3. 快速上手](#3-快速上手)
  - [4. 日常使用与 AI Agent 协作流程](#4-日常使用与-ai-agent-协作流程)
  - [5. 内容保护与隐私边界](#5-内容保护与隐私边界)
- [二、开发者 / 维护者指南（Developers）](#二开发者--维护者指南developers)
  - [1. 仓库结构与详细注释](#1-仓库结构与详细注释)
  - [2. 核心设计：跨库规则、Skills 与全局属性](#2-核心设计跨库规则skills-与全局属性)
  - [3. 对上游 Skills 的集成与覆盖约定](#3-对上游-skills-的集成与覆盖约定)
  - [4. Git 提交与公开前审查规范](#4-git-提交与公开前审查规范)
- [三、第三方来源与许可](#三第三方来源与许可)

---

## 一、使用者指南（Users）

### 1. 这个仓库适合谁

如果你希望参考或复用一套**开箱即用的 Obsidian + AI Agent 共享工作区**：
- **想直接复用配置**：这里有一套经过整理的 `.obsidian/` 行为配置（附件相对路径、自动更新双链、文件忽略规则、`Minimal` 主题偏好、常用社区插件列表与统一属性类型 `types.json`）。
- **想让 AI Agent 安全参与笔记整理**：根目录的 `AGENTS.md` 与 `.agents/skills/` 约束了 Agent 如何读写知识库、如何保护原件和手写笔记、以及如何防止跨库双链误解析。
- **想在一台电脑管理多个独立知识库**：所有实际知识库存放在 `knowledge-base/<库名>/`，被根仓 `.gitignore` 完全隔离，每个库各自维护本地 Git，默认不上传。

---

### 2. 核心组织模型：公共配置层 × 私有知识库层

```text
D:\obsidian\（Vault 根目录 / 公开配置仓库）
├── 公共层（受根 Git 管理）
│   ├── .obsidian/          # 共享 Obsidian 配置、属性类型、启用插件清单
│   ├── .agents/skills/     # 8 个标准化的 Agent 技能包
│   ├── AGENTS.md           # 全局工作规则与公私隔离边界
│   └── THIRD_PARTY_NOTICES.md
└── 私有层（被 .gitignore 忽略）
    └── knowledge-base/     # 存放你自己的各个独立知识库
        ├── 库 A/           # 独立 .git、库内规则与资料
        └── 库 B/           # 独立 .git、库内规则与资料
```

当你使用 **融合 LLM Wiki** 这类面向 Agent 的库结构时，单个知识库内部通常按权责分层：
- **原始资料层**（如 `raw/`、`Clippings/`）：存放原始文章、剪藏与资料附件，**原件保持名称、位置和内容不变**。
- **人工笔记层**（如 `Notes/`）：存放手写笔记与个人思考，受人工所有权保护。
- **Agent 生成层**（如 `wiki/`、`reports/`）：仅带 `managed_by: agent` 标记的页面由 AI Agent 维护，并保留可追溯来源链接。

---

### 3. 快速上手

1. **克隆本配置仓库作为 Vault 根目录**：
   ```bash
   git clone https://github.com/psiQAQ/obsidian-agent-wiki.git
   ```
   用 Obsidian 选择 **打开本地仓库**，选中克隆后的根目录。

2. **按需安装社区插件与主题**（本仓不分发第三方插件本体与主题文件）：
   - 打开 **设置 → 第三方插件**，安装你需要的插件。`.obsidian/community-plugins.json` 中记录了作者日常启用的插件清单：
     - `knowledge-base-manager`（多库管理、单库 Git、库模板与体检）
     - `obsidian-git`、`dataview`、`templater-obsidian`、`quickadd`
     - `obsidian-tasks-plugin`、`obsidian-meta-bind-plugin`、`obsidian-spaced-repetition`
     - `obsidian-excalidraw-plugin`、`obsidian-minimal-settings`、`realclaudian`
     - `gogoga-table`、`gogoga-outline`、`gogoga-mindmap`
   - 外观配置默认选用 **Minimal** 主题（需在 Obsidian 外观中自行下载安装）。

3. **放入或新建你的知识库**：
   - 所有私有知识库建议统一放在 `knowledge-base/<库名>/` 下（该目录已被 `.gitignore` 整目录忽略）。
   - 如果安装了 `Knowledge Base Manager`，可直接通过右侧栏向导创建或接管知识库；如果不使用该插件，也可以直接在 `knowledge-base/<库名>/` 下按普通子目录或独立 Git 仓库组织。

---

### 4. 日常使用与 AI Agent 协作流程

#### ① 新建笔记与附件存放
- 当前 `.obsidian/app.json` 配置 `newFileLocation: "root"`，即快捷键默认在 Vault 根新建文件。建议在具体知识库的笔记目录（如 `knowledge-base/<库名>/Notes/`）中右键新建笔记，避免散落在根目录。
- `.obsidian/app.json` 设置 `attachmentFolderPath: "./assets"`：笔记附件会自动保存至当前笔记旁的 `assets/` 目录中，跟随所属知识库。

#### ② 使用模板与网页剪藏
- **库内模板**：页面模板与库骨架随具体知识库各自维护；若启用了 `Knowledge Base Manager`，可通过命令 **「插入本库页面模板」** 从当前库读取模板并预览属性冲突。
- **Web Clipper 剪藏**：浏览器扩展需单独配置，**Vault** 填 Obsidian 中打开的 Vault 名，**保存位置**填目标库内的剪藏路径（如 `knowledge-base/<库名>/Clippings`），切勿存到根目录共享 `Clippings/`。

#### ③ 与 AI Agent 协作（摄入 / 查询 / 体检）
在支持 `AGENTS.md` 的 AI 工具（如 Claude / Codex / Gemini / OpenCode 等）中打开本 Vault 根目录：
- **始终先明确指定目标知识库**：Agent 会先读取根 `AGENTS.md`，再读取目标库自身的 `README.md` / `kb.toml` / `AGENTS.md` 与对应 Skill。
- **普通查询不写文件**：询问已有结论时，Agent 仅检索并引用来源作答。
- **明确指令才触发摄入或维护**：如「将 `<库名>/Clippings/` 下的新文章摄入到 `<库名>`」，处理完成后原件留在原地。

---

### 5. 内容保护与隐私边界

- **严格单库边界**：默认只在你指定的知识库内检索与写入，禁止未经授权跨库读取、引用或搬运内容。
- **原件与人工笔记保护**：未明确标注 `managed_by: agent` 的内容均视作人工内容；原始资料层保持只读。
- **根仓永不提交私人数据**：`knowledge-base/`、`.kb-manager/`、`.claudian/`、根级 `assets/`、`Clippings/` 及个人工作区状态文件均在 `.gitignore` 中被排除。

---

## 二、开发者 / 维护者指南（Developers）

### 1. 仓库结构与详细注释

```text
obsidian-agent-wiki/                 # Obsidian Vault 根目录（同时作为个人公开配置 Git 仓库）
│
├── AGENTS.md                        # [受跟踪] 根级与跨库工作契约：读取顺序、多库隔离、内容所有权、
│                                    #          Web Clipper 边界、模板/体检规范、Git 与公开边界
├── README.md                        # [受跟踪] 正式仓库说明文档
├── README-GEMINI.md                 # [待审草稿] 本说明文档草稿（供审阅与合并评估）
├── THIRD_PARTY_NOTICES.md           # [受跟踪] 第三方材料来源、上游核对提交与 MIT 许可声明
├── skills-lock.json                 # [受跟踪] .agents/skills/ 技能锁文件（来源仓库、路径与 SHA256）
├── .gitignore                       # [受跟踪] 私有库、插件本体、个人工作区与缓存隔离规则
│
├── .agents/                         # AI Agent 通用能力目录
│   └── skills/                      # [受跟踪] 保留上游原样的 8 个技能包（定制规则统一写在 AGENTS.md）
│       ├── karpathy-llm-wiki/       #   LLM Wiki 工作流、示例、模板及 scripts/check_evidence.py
│       ├── obsidian-markdown/       #   Obsidian Markdown 语法（双链、Embeds、Callouts、Properties）
│       ├── obsidian-bases/          #   .base 数据库视图、筛选器与公式参考
│       ├── obsidian-cli/            #   Obsidian CLI 交互与插件/主题调试
│       ├── obsidian-headless/       #   无桌面端环境的 Obsidian Sync / Publish CLI (ob)
│       ├── json-canvas/             #   .canvas 白板 JSON 格式与示例
│       ├── defuddle/                #   HTML 转干净 Markdown 的 Defuddle CLI 指南
│       └── knap/                    #   基于模板与 JSON/CSV 批量生成 Markdown 笔记
│
├── .obsidian/                       # Obsidian Vault 共享配置（仅跟踪通用配置，忽略插件本体与个人状态）
│   ├── app.json                     # [受跟踪] 编辑器与链接：./assets 附件、alwaysUpdateLinks、userIgnoreFilters
│   ├── appearance.json              # [受跟踪] 外观配置：Minimal 主题、界面与字体动作设置
│   ├── core-plugins.json            # [受跟踪] 核心插件开关（启用 bases、properties、templates、sync、graph 等）
│   ├── community-plugins.json       # [受跟踪] 作者启用的 14 个社区插件 ID 清单
│   ├── templates.json               # [受跟踪] 核心模板插件日期格式（YYYY-MM-DD）与全局目录配置
│   ├── types.json                   # [受跟踪] Vault 级统一属性类型 Schema（避免跨库同名属性类型冲突）
│   ├── plugins/                     # [规则控制] .gitignore 忽略 */* 插件发行文件，仅默认放行 data.json
│   │   ├── obsidian-excalidraw-plugin/data.json      # [受跟踪] Excalidraw 公开安全配置
│   │   ├── obsidian-minimal-settings/data.json       # [受跟踪] Minimal 主题公开安全配置
│   │   └── knowledge-base-manager/data.json          # [显式忽略] 避免私人设备/库偏好泄露
│   ├── themes/                      # [忽略] 本地安装的 CSS 主题文件（如 Minimal、Obuntu、VSCode 2026）
│   ├── workspace*.json              # [忽略] 窗口布局与打开页面状态
│   ├── graph.json / bookmarks.json  # [忽略] 个人图谱与书签状态
│   └── hotkeys.json / note-composer.json / page-preview.json  # [本地未跟踪] 按需本地状态
│
├── .vscode/
│   └── settings.json                # [受跟踪] 多仓扫描深度（git.repositoryScanMaxDepth: 2）与 Conda 环境配置
│
├── .kb-manager/                     # [忽略] Knowledge Base Manager 的本机库登记状态（如 libraries.json）
├── knowledge-base/                  # [忽略] 所有个人/专题知识库目录，各子库独立使用本地 Git
├── .claudian/ .cache/               # [忽略] AI 客户端本地目录与缓存
└── /assets/ /Clippings/             # [忽略] 防止根目录未归类附件或剪藏误提交
```

---

### 2. 核心设计：跨库规则、Skills 与全局属性

1. **配置与规则分层**：
   - **Vault 级（本仓库）**：通过 `.obsidian/` 统一编辑器体验与属性类型，通过 `AGENTS.md` 定义全局不可逾越的安全边界（不改原件、不越权改人工笔记、不泄露隐私）。
   - **知识库级（`knowledge-base/<库名>/`）**：每个库可拥有自己的 `AGENTS.md`、`README.md`、`kb.toml`（目录映射）与独立模板，各自独立演化。
2. **统一属性 Schema（`.obsidian/types.json`）**：
   因为 Obsidian 的属性类型对整个 Vault 生效，`.obsidian/types.json` 预设了常用属性类型以确保多库兼容：
   - **AI 与来源追踪**：`managed_by` (`text`)、`sources` (`multitext`)、`source_url` (`text`)、`snapshot_source_note` (`text`)、`snapshot_source_mtime_ns` (`text`)
   - **组织与生命周期**：`type` (`text`)、`status` (`text`)、`categories` (`multitext`)、`tags` (`tags`)、`aliases` (`aliases`)、`cssclasses` (`multitext`)、`created` / `updated` / `archived` / `collected` / `published` (`date`)
   - **任务查询兼容**：`TQ_*` 系列 `checkbox` / `text` 类型

---

### 3. 对上游 Skills 的集成与覆盖约定

`.agents/skills/` 中的 8 个技能均保留上游原始文件（可通过 `skills-lock.json` 与 `THIRD_PARTY_NOTICES.md` 核对内容哈希与对应上游提交）。维护本仓库时应遵循：**不直接修改上游 Skill 文件，而是通过 `AGENTS.md` 声明覆盖规则**：

- **目录布局替代**：允许库级目录映射替代固定 `raw/` + `wiki/` 两层布局与单层主题限制。
- **全路径双链**：Agent 生成双链须使用从 Vault 根起的完整目标路径，防止其他库中的同名文件参与解析。
- **内容与历史分离**：现行结论与历史归档分开，新来源按标题保存，有新增内容或争议才建摘要；来源文件始终只读。

---

### 4. Git 提交与公开前审查规范

由于本仓库既是工作 Vault 又是公开配置仓库，提交根仓前务必完成以下核对：

1. **检查配置与插件隐私**：
   - `.obsidian/plugins/` 仅允许放行确认不含 **API Key、Token、私人路径、邮箱或服务地址** 的 `data.json`；插件发行本体（`main.js`、`manifest.json` 等）不入库。
   - 不要将个人的主题微调、临时工作区改动混入功能提交。
2. **核对忽略边界未被突破**：
   - 确保 `knowledge-base/`、`.kb-manager/`、`.claudian/` 及任何私有附件未进入暂存区。
3. **提交前执行核对命令**：
   ```bash
   git status --short
   git diff --cached --name-status
   git diff --cached
   ```
4. **同步第三方声明**：更新 `.agents/skills/` 后，需同步更新 `skills-lock.json` 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

---

## 三、第三方来源与许可

本仓库中第三方 Skills 与参考模板的来源、核对提交号及 MIT 许可声明，以及部分历史参考材料的待核对记录，均完整记载于 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
