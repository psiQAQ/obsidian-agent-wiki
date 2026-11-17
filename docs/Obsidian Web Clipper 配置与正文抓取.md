# Obsidian Web Clipper 配置与正文抓取

以下操作在浏览器和浏览器扩展 Obsidian Web Clipper 的设置中完成。

## 设置保管库

打开扩展设置的 **常规 → 保管库**，填写与 Obsidian 中显示名称完全一致的保管库名称，例如 `obsidian`。这个字段填写 Obsidian 打开的 Vault 目录的名称，而不是保存目录的完整地址。

## 复制默认模板

选中扩展自带的默认模板（default），点击右上角 **更多 → 复制**，在副本上修改。这样可以沿用默认属性及其提取配置；新建空白模板时则需自行补充这些配置。

可以复制多份，按知识库或网站分别命名和配置。

## 配置模板

|  | 配置项 | 推荐设置 |
| :---: | --- | --- |
| 模板 | 模板名称 | 使用便于辨认的名称，例如服务于某一个知识库 `xxx研究` 或者针对某一个网站 `GitHub文档`。 |
|  | 模板触发器 | （可选）填网站的 Base URL，例如 `https://docs.github.com`；页面网址匹配该前缀时自动选用此模板。 |
| 位置 | 保管库 | 选择刚添加的实际保管库，例如 `obsidian`。 |
|  | 笔记位置 | 填知识库相对于保管库的目录，例如 `knowledge-base/xxx研究/Clippings`。 |
|  | 笔记名称 | 可沿用 `{{title}}`。 |
|  | 行为/保存方式 | 选择 **Create a new note**；重名时使用独立文件名，保留每份原件。 |
| 内容 | 属性 | 沿用默认模板提供的属性与提取配置，核对来源网址、作者、发布日期和剪藏时间等信息。 |
|  | 笔记内容 | 先使用默认正文提取，当获取不到正文时，补全方式按下文的 CSS 选择器方式调整。 |
<!-- gogoga-table: {"w":[null,129,573],"merge":["A4:A7","A2:A3","A8:A9"]} -->
> 已保存到本地 markdown 中顶部带有 `source`、`clipped` 等属性，分别用于追溯来源与剪藏时间。

## 用 GitHub 文档检查抓取效果

推荐用 GitHub 文档的[“什么是 GitHub？”](https://docs.github.com/zh/get-started/start-your-journey/what-is-github)作为练习页：

1. 打开网页和 Web Clipper，确认选中了刚配置的模板、保管库和笔记位置。
2. 在剪藏预览中对照网页，检查标题、各节正文和文中的链接是否齐全。
3. 保存后打开 `knowledge-base/xxx研究/Clippings/` 中的 Markdown 文件，再核对正文结构和来源属性。

> 视频页面优先选择带字幕的内容，保存后核对实际获得的字幕及其范围；提取效果取决于网站支持情况。

## 用 CSS 选择器补全正文

正文有遗漏时，可以将网站交给 AI，结合页面结构调整模板中的 **笔记内容（Note content）**。通过 CSS 选择器定位文章主体，再将对应 HTML 转为 Markdown，例如：

```text
{{selectorHtml:article|markdown}}
```

这里以 `article` 为候选正文容器演示语法，实际选择器需根据目标网页结构确认。`selectorHtml` 提取元素的 HTML，`markdown` 将其转换为 Markdown，便于保留标题、列表、链接、表格和代码结构。

> [官方变量文档](https://help.obsidian.md/web-clipper/variables)使用 `{{content}}` 表示正文。现有模板若写着 `{{context}}`，先核对该字段的用途，再调整笔记内容中的提取表达式。模板触发方式见[官方模板文档](https://help.obsidian.md/web-clipper/templates)。

可以把下面的提示词交给 AI，并填写实际页面、缺失内容和当前配置：

```text
我正在使用 Obsidian Web Clipper（https://obsidian.md/zh/clipper），
希望将网页正文完整保存为本地 Markdown。

目标网页：[填写出现正文遗漏的网址]
缺失内容：[描述遗漏的段落、列表、表格或代码块]
当前保存结果：[粘贴相关 Markdown 片段]

请结合目标网页的实际 DOM 或我提供的 HTML 片段：
1. 定位文章主体的 CSS 选择器，说明覆盖范围与匹配数量，优先使用稳定的语义标签或属性。
2. 给出可直接填入“笔记内容”的 Web Clipper 表达式，
   例如 {{selectorHtml:实际选择器|markdown}}，保留正文的标题、列表、链接、表格和代码结构。
```

## 保存位置排错与后续摄入

出现 `vault not found` 时，依次核对扩展设置中的保管库名称、剪藏弹窗的选择、当前模板的目标保管库，以及笔记位置是否为 Vault 内相对目录。以目标文件夹中出现文件且正文可打开为保存成功的标志。

保存并核对内容后，可向 Agent 发出请求：

```text
请阅读 knowledge-base/xxx研究/Clippings/示例网页.md，
先与我讨论值得积累的内容，再按确认范围摄入，保留剪藏原件和来源信息。
```
