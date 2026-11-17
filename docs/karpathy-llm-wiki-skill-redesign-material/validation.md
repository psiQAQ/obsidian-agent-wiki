# 融合模板实施验收

验收日期：2026-11-16。范围是本地规则、模板、共享配置、初始化和只读检查工具；没有迁移现有知识库，也没有发布到 GitHub。

规则阶段提交为 `1b5ad2b`，模板及子模块阶段提交为 `e204a54`。环境和脚本版本以包含本文的提交为准。环境为 Windows、Python 3.14.5、PyYAML 6.0.3、Obsidian 1.15.1；Steph 子模块固定在 `473697347a0eaac790a6596229c741b3915f3b77`，工作区无改动。

## 已完成的检查

| 结果 | 类型 | 范围与观察 |
| --- | --- | --- |
| Passed | 文档静态检查 | 25 项选择均有四方立场、最终选择和覆盖说明；根 AGENTS 为 4478 字符，低于 8000 字符。原始 Skill 未修改。 |
| Passed | 实际运行 | 26 项 unittest 通过，包含中文和空格名称、人工复制与本地 Git 初始化、拒绝覆盖、路径越界、可变目录映射及错误配置返回码。 |
| Passed | 实际运行 | 来源路径、同名页面隔离、属性双链、缺失证据、No material 日志识别、索引日期及只读行为均有回归用例；来源标题中的 `#` 按实际文件名处理。 |
| Passed | 隔离样例 | 人工笔记整理至 Notes 后补全缺失属性并修复引用链接，已有属性和正文不变，原件内容不变。测试模拟 Agent 的整理步骤，没有添加自动改写人工笔记的接口。 |
| Passed | 隔离样例 | 保存分析使用原件来源，归档使用知识页来源；来源更新日期晚于归档时提示可能过时，检查器保持快照内容不变。内容更新仍由 Agent 执行。 |
| Passed | 实际运行 | `uv run --no-sync python scripts/check_kb.py knowledge-base-template/llm-wiki` 返回 0，输出 0 errors、0 review items；测试库 A、B 也均返回 0。 |
| Passed | 实际 Obsidian 界面 | A、B 中放置同名页面；A 的生成知识视图只显示 A 的记录。修正过滤后显示 4 条，其中“模板设计”正常出现，页面模板未混入。公共模板视图显示 0 条结果。 |
| Passed | 实际 Obsidian 界面 | 人工笔记视图限定 A 库；属性正常呈现，带完整库路径的分类关系可见；正文来源链接打开 A 自己的原文。 |
| Passed | 实际 Obsidian 界面 | 共享人工笔记模板插入成功，生成日期和 `managed_by: human`；插入的 115 字节 SVG 正常显示，落在测试库的 `Notes/assets/attachment.svg`。 |
| Passed | Git 静态检查 | 整个 knowledge-base、环境、缓存、工作区、书签和图谱状态被忽略；模板保留许可。共享 app.json 只提交本次附件设置，用户原有设置、插件、主题和参考材料保持未提交。 |

复现自动检查：在仓库根目录运行 `uv run --no-sync python -m unittest discover -s tests -v`。

> 测试只在根 `.cache/tests/` 中创建和清理样例。真实知识库未作为测试输入。

## 失败记录及处理

- **环境阻止启动，后续 Passed**：沙箱内启动已有 Python 环境曾返回 `error: uv trampoline failed to spawn Python child process` 和 `permission denied (os error 5)`，测试当时未启动。通过已获准的普通用户执行完成验收；没有重装 Python 或依赖，也没有修改系统权限。
- **CLI 路径 Not Run，实际界面验证 Passed**：Obsidian CLI 返回 `Command line interface is not enabled. Please turn it on in Settings > General > Advanced.`。保留原设置，改用已运行的桌面应用完成验收，不将 CLI 不可用记作模板失败。
- **界面操作中断，后续 Passed**：原生附件选择对话框的控件定位未成功；重新观察后确认文件名并用键盘提交，最终文件位置和显示均已验证。
- **静态检查发现，已修正**：清除了人工笔记模板的多余末尾空行；Bases 改为排除模板目录，避免误隐藏名称包含“模板”的知识页；非法 TOML 路径表统一返回配置错误码 2。

## 使用限制与清理

证据脚本是线索检查器。定性事实、普通短整数、释义、计算和上下文需要逐条阅读原文；字符串匹配不等于语义验证。PDF、图片等非文本证据只报告需要另外核查，不自动执行 OCR。未使用真实私人资料进行内容质量验收。

> Bases 不读取 `kb.toml`。更改模板目录时需同步修改两处模板目录过滤条件，方法见融合模板 README；其他目录映射由脚本读取。

本次临时库 `knowledge-base/LLM 验收 A`、`knowledge-base/LLM 验收 B` 与仓库内临时脚本、uv 缓存均在验收后清理；根 `.venv` 是交付环境，予以保留。没有仓库外临时文件或超大文件待清理。

GitHub 发布 **Not Run**：按已批准的本地实施范围，根仓库不设置 remote、不 push、不发布；不影响本地使用。

## 2026-11-16：按需分类入口补充验收

本次新增通用分类入口模板和专用 Base 样板，同步规则、选择记录及模板 README。既有总览及其未提交的用户排序修改保留，不纳入本次提交；没有预建任何生活类别或修改现有知识库。

- **Passed（静态及实际运行）**：新 Base YAML 可解析；实例化后的分类页属性、索引、嵌入和类别链接通过检查；根 AGENTS 仍低于 8000 字符。融合模板检查输出 0 errors、0 review items。
- **Passed（实际 Obsidian 1.15.1）**：两个临时库各有同名类别和不同成员；A 的类别页嵌入及直接打开专用 Base 均只显示 `A-member` 这 1 条记录，A 的其他类别及 B 的成员均未混入。B 的笔记嵌入 A 的专用 Base 显示 0 条结果，确认上下文限制生效。
- **首次样例断言 Failed，后续已处理**：初始脚本要求完全无提醒，实际检查器正确返回 `empty-overview`：`knowledge exists; review whether the initial overview should be populated`。样例只创建分类导航，没有生成领域综述；后续明确验证此预期提醒，未修改检查器或放宽产品校验。终端显示中文路径时出现乱码，改用仓库内 UTF-8 脚本保存和执行验收逻辑。
- 本次无运行代码或依赖变更，复用原有回归结果，只补做模板结构及实际视图验证。临时库 `分类验收A`、`Category-QA-A`、`Category-QA-B` 和 `.cache/category-validation/` 验收后清理，没有仓库外清理项。

## 2026-11-16：独立 Clippings 剪藏目录

新增每库 `Clippings/` 及可选 `paths.clippings` 映射；与 raw 一并作为不可改写的来源层。同步 Web Clipper 接入说明、根规则和选择记录；没有安装扩展、修改浏览器设置或迁移现有知识库。

- **Passed（实际运行）**：30 项 unittest 全部通过。新增用例覆盖剪藏引用和证据线索、原件字节不变、不误报人工笔记、待摄入识别、No material 日志、缺失目录提醒、自定义目录、旧配置兼容、路径越界与重叠拒绝、跨库来源及日志拒绝。
- **Passed（实际运行）**：融合模板检查输出 0 errors、0 review items；模板复制与初始化用例仍通过，新库包含独立 Clippings。
- **Not Run（浏览器端剪藏）**：本次范围为模板与接入文档，不包含安装扩展或修改用户浏览器配置；未执行真实网页剪藏。保存路径与模板行为根据官方 Web Clipper 页面及模板帮助核对，首次使用须按模板 README 设置并确认落盘位置。
- 临时测试样例由测试自动清理，无仓库外产物、无依赖变更；已有配置、总览排序及插件修改保持未提交。
