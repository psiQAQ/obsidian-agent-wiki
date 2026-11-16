# {{kb_name}}

{{description}}

## 从这里开始

- [知识索引](wiki/index.md)：已编译页面及摘要。
- [综述](wiki/overview.md)：从摄入资料逐步形成的领域与综合判断。
- [属性视图](knowledge.base)：按当前知识库查看生成知识、人工笔记和类别。
- [操作日志](wiki/log.md)：摄入、保存、归档与体检记录。

网页剪藏放入 `Clippings/`，其他原始资料放入 `raw/`，自己的笔记放入 `Notes/`。在 Obsidian 中从目标库的 `Notes/` 文件夹新建笔记，再插入共享的“人工笔记”模板。附件默认保存在当前笔记旁的 `assets/`。

向 Agent 明确说出库名和任务，例如“在这个知识库摄入 raw 中的这份资料”。单份先讨论要点；需要处理多份时明确要求批量。普通提问不写文件，需要积累时说“保存”，保留历史快照时说“归档”。

## 目录和维护边界

`kb.toml` 记录本库目录映射。需要调整目录时，先约定布局，再一起更新映射、README、索引和相关链接；`Notes/` 统一保留。Bases 不读取 TOML，若改动模板目录，还须同步修改 `knowledge.base` 中排除 `/templates` 的两处过滤条件。本库遵循共享仓库根 `AGENTS.md`；额外领域规则可在这里说明，规则变化须用户确认。

- 原始资料保持内容、名称和位置，不为补属性改写原件。
- `managed_by: agent` 标记可由 Agent 维护的知识。没有该标记的已有笔记默认按人工内容保护。
- 人工笔记错放时可整理到 `Notes/`，补全缺失属性、修链接，保留原有属性和正文观点。归属不清或重名先询问。
- 各库默认独立检索和维护；属性中的新双链写明完整 Vault 相对路径，不依赖其他库同名文件。

## 使用 Obsidian Web Clipper

[Web Clipper](https://obsidian.md/zh/clipper) 是浏览器扩展，可通过自己的模板自定义剪藏内容、属性和保存位置。它的模板在浏览器扩展内配置，与本库 `templates/` 中供 Obsidian Templates 使用的 Markdown 模板不同。

以共享 Vault 中的 `knowledge-base/研究示例/` 为例，在 Web Clipper 的模板设置中：

1. Vault 选择打开本仓库根目录的那个 Vault，而不是把每个知识库当成单独 Vault。
2. Note location 填 `knowledge-base/研究示例/Clippings`；Note name 可使用 `{{title}}`。每个常用知识库可复制一份 Clipper 模板并明确命名；保存前核对目标库。
3. Behavior 使用创建新笔记，正文保留网页内容。重名时使用区分名称，不覆盖或追加到已作为证据引用的原件。新取得的网页版本另存，再由 Agent 比较。
4. 尽量保留原始网址、标题、作者、发布日期和剪藏日期。已有 Clipper 的 `source`、`clipped` 等字段原样保留；缺失信息在摄入日志补充，不为匹配本库属性改写原件。未知发布日期不猜测。
5. 保存后应在该库 `Clippings/` 看见 Markdown 文件；再向 Agent 指定该文件摄入，或明确要求批量处理该库剪藏。剪藏不会自动触发摄入。生成知识的 `sources` 可写 `../Clippings/文章标题.md`，正文链接须将空格等字符 URL 编码。

`raw/` 与 `Clippings/` 都是原始资料层。摄入后不移动原件；`No material` 日志的 `Raw` 链接也可指向 Clippings。检查器会识别未引用且未记录为 No material 的剪藏，不把它们列为错放人工笔记。网页中的远程图片链接不代表已下载附件，需要离线保存时另行核对并放在所属库内。

`kb.toml` 的 `clippings = "Clippings"` 可随库布局调整。旧库未配置该键时继续按原规则工作；启用时自行建立目录并添加映射，不自动迁移已有资料。浏览器扩展中的模板不会随根 `.obsidian/` 配置自动完成设置。

依据：[官方模板设置说明](https://obsidian.md/help/web-clipper/templates)，查阅日期 2026-11-16。本次提供目录及接入说明，不安装扩展或改动浏览器设置。

## 按需建立独立分类入口

现有 `knowledge.base` 保留全库总览。需要某个类别的导读、阅读顺序或专用字段时，再建立入口页和专用 Base；不需要预装整套生活分类。

例如在 `knowledge-base/研究示例/` 中建立“方法”入口（以下目录使用默认映射，改过布局时按 `kb.toml` 调整）：

1. 在 `wiki/方法.md` 插入共享“分类入口模板”，填写标题与日期。人工复制模板时手动替换 `{{title}}` 和日期占位符。纯导航保留空 `sources`；加入事实性说明时补充原件来源。
2. 创建 `wiki/bases/`，复制 `templates/Bases/分类专用模板.base` 为 `wiki/bases/方法.base`。不覆盖已有文件。
3. 在新 Base 中替换全部占位符：`__KB_ROOT__` → `knowledge-base/研究示例`，`__WIKI_DIR__` → `wiki`，`__TEMPLATES_DIR__` → `templates`，`__CATEGORY_PATH__` → `knowledge-base/研究示例/wiki/方法`（不含 `.md`）。路径均使用 `/`，不加末尾斜杠；路径含引号时须按 Bases 字符串及 YAML 规则转义。
4. 把入口页中的 `__BASE_PATH__` 替换为 `knowledge-base/研究示例/wiki/bases/方法.base`。将成员页的 `categories` 设置为包含 `"[[knowledge-base/研究示例/wiki/方法]]"` 的列表；不要使用可能指向其他库的短名称。
5. 将分类入口加入本库索引，填写摘要及与页面一致的更新时间，并在本次操作日志中记录。按用途调整专用 Base 的列、排序或增加视图，保留顶层范围和类别过滤。
6. 打开入口页及 Base，确认只显示本库该类别的成员；其他类别、其他库同名类别不应出现。在其他库嵌入该 Base 时也应为空。运行根目录检查器核对属性、索引和链接；检查器不执行 Base 表达式，过滤行为须在 Obsidian 中确认。

默认分类视图只展示生成知识。需要展示人工笔记时先约定范围，再增设明确限定本库 `Notes/` 的视图，不因展示获得修改人工内容的权限。类别页、库名或目录改名后，须同步修改成员属性、嵌入路径和 Base 的绑定路径；不能只依赖自动更新链接。

## 初始化与版本管理

这个模板应复制到共享 Vault 的 `knowledge-base/<库名>/`。脚本初始化会填写本文件并执行 `git init`。人工复制时修改文件夹名、本文件标题和简介，然后在新库执行 `git init`；不复制其他库的 `.git` 或 `.obsidian`。

本库使用独立本地 Git，默认不设置 remote、不上传。目录、日期、来源均以文本保留，正文相对链接可随库一起迁移；Bases 与属性双链面向共享 Vault，单独迁出 Vault 后需调整该部分入口。

通用页面模板在 `templates/`，原始资料和个人内容不写入公共模板。第三方模板的许可见 [LICENSES.md](LICENSES.md)。
