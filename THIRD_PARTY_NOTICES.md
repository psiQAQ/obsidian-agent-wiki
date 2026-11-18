# 第三方来源与许可

本文只记录第三方材料的来源与许可，不指定本仓库自主新增内容的整体发布许可，也不把软件许可扩大到另存的外部文章。

## Karpathy LLM Wiki

融合模板的摄入、查询、归档与体检规则，以及旧版证据检查器的数字、日期、引语候选及边界匹配方法，改编自 [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) 的相应规则与 `scripts/check_evidence.py`。原始 Skill 保留在 `.agents/skills/karpathy-llm-wiki/`，融合规则继续由本仓库维护。历史实现见[旧版证据检查器](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/scripts/evidence.py)。

2026-11-17 核对[上游提交 eafcc770](https://github.com/Astro-Han/karpathy-llm-wiki/tree/eafcc77001e496cc43499e4923b663aec722c813)：本地原始 Skill 的 `SKILL.md`、`scripts/check_evidence.py`、`LICENSE` 与该版本一致（比较时仅统一 LF/CRLF）。本节 MIT 许可来自该版本的 [LICENSE](https://github.com/Astro-Han/karpathy-llm-wiki/blob/eafcc77001e496cc43499e4923b663aec722c813/LICENSE)，不据此推断原始 Gist 或中文改版全文的授权。

MIT License

Copyright (c) 2026 Yuhan Lei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Obsidian Skills

本地 `.agents/skills/` 中的 `defuddle`、`json-canvas`、`knap`、`obsidian-bases`、`obsidian-cli`、`obsidian-headless`、`obsidian-markdown` 来自 [obsidianmd/obsidian-skills](https://github.com/obsidianmd/obsidian-skills/tree/caf3e98cd22d810db164f26c9a442f0a280daa43)。2026-11-17 将这七个目录中的全部 12 个文件与该固定提交比较，除 LF/CRLF 外内容一致；本地副本和锁文件未改动。

以下保留该版本的 [MIT 许可](https://github.com/obsidianmd/obsidian-skills/blob/caf3e98cd22d810db164f26c9a442f0a280daa43/LICENSE)：

MIT License

Copyright (c) 2026 Steph Ango (@kepano)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Steph Ango 参考模板

模板来源与 MIT 许可保留在上游子模块及融合模板的 [LICENSES.md](knowledge-base-template/llm-wiki/LICENSES.md)。模板许可不等于 Steph Ango 网站文章的全文再发布授权。

## 尚未确认的全文来源记录

以下材料的原件保存在本地项目档案库。表中材料链接定位到迁移前的公开提交，署名和全文再发布许可仍按各项记录核对。

| 历史材料 | 已有来源信息 | 待确认项 |
| --- | --- | --- |
| [LLM Wiki 原始说明](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/docs/karpathy-llm-wiki-skill-redesign-material/llm-wiki.md) | 原件末尾记录 [Karpathy Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#file-llm-wiki-md)。 | 本地副本对应版本及全文再发布许可。 |
| [中文改版](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/docs/karpathy-llm-wiki-skill-redesign-material/第二大脑知识库%20中文版.md) | 原件末尾记录[飞书来源链接](https://ucn476nzwurg.feishu.cn/wiki/MhuQwtkodizeJqklPcLc4hTQnjd)，并带有自己的日期属性。 | 作者、对应版本及全文再发布许可；不把文件日期当作已核实的发布日期。 |
| [How I use Obsidian](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/docs/karpathy-llm-wiki-skill-redesign-material/How%20I%20use%20Obsidian%20Steph%20Ango.md) | 原件记录 [Steph Ango 原文](https://stephango.com/vault)。 | 本地副本对应版本及文章全文再发布许可。 |
| [X 推文副本](https://github.com/psiQAQ/obsidian-agent-wiki/blob/592dd626be508e65316368533c980bdf77003969/docs/karpathy-llm-wiki-skill-redesign-material/X.md) | 原件已注明复制自推文，作者、链接和发布时间尚未记录。 | 原推文出处、版本及全文再发布许可。 |
