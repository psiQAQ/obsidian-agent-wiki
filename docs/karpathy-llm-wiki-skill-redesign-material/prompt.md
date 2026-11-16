# karpathy-llm-wiki 优化

本仓库中 karpathy-llm-wiki 的 skill 是基于 docs\karpathy-llm-wiki-skill-redesign-material\llm-wiki.md （原始 Gist 的理念）文档 由 [Astro-Han](https://github.com/Astro-Han) 开发的一个 skill，同时 docs\karpathy-llm-wiki-skill-redesign-material\第二大脑知识库 中文版.md 是我从网上找到的llm-wiki.md 的改版。docs/karpathy-llm-wiki-skill-redesign-material/How I use Obsidian Steph Ango 则是我从 obsidian 的 CEO Steph Ango（kepano）组织笔记和资料的方式的文档，同时 knowledge-base-template/kepano-obsidian 中存放了他使用的 Vault 模板（把这个模板的 git 仓库改为本仓库的子模块并支持更新）。

如果要将 原始 Gist 的理念 与 中文版 md 与 karpathy-llm-wiki 与 Steph Ango 理念及其模板的基础上进行融合，当同一个概念或者实现操作如果有冲突，则全部以提问方式逐个向我询问要保留其中的某一个，你将我的选择(参见模板)最终汇总成一份文档保留在本文档同目录下的 redesign-choice.md 文档中，之后你在根目录生成一份 AGENTS.md 来指导后续工作。

当选择的规则与 skill 的规则冲突时，在 AGENTS.md 中进行说明以 AGENTS.md 为准覆盖 skill。当涉及脚本问题时，在本仓库建立 scripts 文件夹来运行。

以下内容也写入 AGENTS.md 中：

- 本仓库根目录创建 uv python 3.14 环境，安装必要库；
- 本仓库作为 obsidian 软件与 agent 交互的桥梁，根目录的 knowledge-base 文件夹作为知识库的顶层，每个其下的文件夹存放多个独立方向的知识库，并每个知识库各自通过 git 管理；
- 本仓库除了知识库以外的内容作为一个 obsidian 的知识库管理模板上传到 github 上进行公开，但知识库留在本地默认不上传；
- .obsidian 文件夹作为 obsidian 的配置文件夹，存放 obsidian 的插件和配置等信息，但 git 忽略 bookmarks.json/workspace.json/graph.json 等涉及知识库内容信息的文件；
- 根目录的 knowledge-base-template 文件夹作为知识库的模板文件夹，其下创建一个知识库基础模板，该框架来源于 原始 Gist 的理念 与 中文版 md 与 karpathy-llm-wiki 三者基于我的选择融合后的规则，并将模板上传到 github 上进行公开，当人工或者 agent 创建新的知识库时，直接复制该文件夹，并修改文件夹名称为知识库名称，并修改文件夹下的 README.md 文件，将 README.md 文件作为知识库的简介，进行本地 git init；

注：该仓库搭建的目的是为了解决 obsidian 的配置和 agent 操作可在多个独立知识库之间通用，避免每个知识库都要重新配置一次 obsidian 的问题。

## 我的选择模板

### 1. xxx 问题

- [x] 原始 Gist 的理念：xxx
- [ ] 中文版 md：xxx
- [ ] karpathy-llm-wiki：xxx
- [ ] Steph Ango 理念和模板：xxx

### 2. yyy 问题

- [ ] 原始 Gist 的理念：yyy
- [x] 中文版 md：yyy
- [ ] karpathy-llm-wiki：yyy
- [ ] Steph Ango 理念和模板：yyy

### 3. zzz 问题

- [ ] 原始 Gist 的理念：zzz
- [ ] 中文版 md：zzz
- [x] karpathy-llm-wiki：zzz
- [ ] Steph Ango 理念和模板：zzz
- [ ] 其他：zzz

...
