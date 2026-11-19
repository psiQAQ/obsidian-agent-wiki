# Obsidian 共享 Vault

在 Obsidian 桌面版中将仓库根目录作为 Vault 打开。每个研究方向使用 `knowledge-base/<库名>/` 下独立的知识库，各自保存资料、人工笔记和 Git 历史。根仓库维护共享模板、Agent 技能、规则和可公开的配置。

## 新建知识库

1. 在 Obsidian 桌面版 1.15.1 或更高版本安装并启用 **Knowledge Base Manager**。离线包解压到当前 Vault 的 `.obsidian/plugins/` 后，插件清单应位于 `.obsidian/plugins/knowledge-base-manager/manifest.json`。包含下述两套模板的离线包可从插件开发分支 `feat/library-source-control` 构建。[离线安装说明](https://github.com/psiQAQ/obsidian-kb-manager/tree/feat/library-source-control#离线安装)。
2. 运行 **打开知识库管理器**，在右侧栏选择 **新建**。例如填写目录名「光学研究」，选择 **融合 LLM Wiki** 模板，核对预览中的 `knowledge-base/光学研究` 后点击 **创建**。
3. 将原始资料放入该库的 `raw/`，在 `Notes/` 编写人工笔记。要保存本地版本，在该库行展开 **Git 状态**，核对暂存内容后提交。要检查结构、来源或引用，打开同一行的 **… → 体检**。

创建时也可选择 **Kepano（含示例）**，使用它的分类、示例与本库专用的 Bases。在融合 LLM Wiki 库中，`kb.toml` 记录目录映射。每个新建的融合库都附带 `README.md` 使用手册和 `AGENTS.md` 操作规则，可以在库内查看资料摄入、查询和归档示例。

## 共享模板与技能

共享页面模板位于 [templates/](templates/)。在 Obsidian 命令面板运行 **模板：插入模板**，可选用人工笔记、知识页面、资料摘要等六个 Markdown 模板。`templates/Bases/分类专用模板.base` 供建立分类视图时复制。要使用当前知识库自己的模板，先打开该库内的 Markdown 笔记，运行 **插入本库页面模板**，选择模板并核对目标笔记、属性与正文预览，再确认插入。已有同名属性保留原值。Vault 的 Agent 技能位于 `.agents/skills/`。操作前先确定目标知识库，按[仓库规则](AGENTS.md)和该库规则读取资料。第三方材料的作者与许可见[来源记录](THIRD_PARTY_NOTICES.md)。

## 旧项目资料

本地知识库 `knowledge-base/Obsidian 项目档案/` 的 `raw/README.md` 与 `raw/docs/` 保存原始文档，`reports/` 内有迁入清单。这个知识库有自己的本地 Git，克隆根仓库只能取得公开材料。原使用说明、Web Clipper 指南、设计与验收文档仍可在历史提交中查阅。[原 README](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/README.md) · [原文档目录](https://github.com/psiQAQ/obsidian-agent-wiki/tree/592dd626be508e65316368533c980bdf77003969/docs)
