"""Acceptance/regression cases using only repository-local disposable fixtures."""

from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

import yaml


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from check_kb import inspect, inspect_snapshots, main as check_main
from evidence import candidates, contains
from init_kb import bind_overview, initialize
from kb_common import ConfigError, KnowledgeBase, read_note
from markdown_links import parse_markdown


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def note(path, body, **changes):
    metadata = dict(type="concept", managed_by="agent", categories=[], tags=[], aliases=[], created="2026-11-16", updated="2026-11-16", sources=["../raw/原始 资料.md"])
    metadata.update(changes)
    put(path, "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n\n" + body)


class WikiCase(unittest.TestCase):
    def setUp(self):
        cache = REPO / ".cache" / "tests"
        cache.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=cache, prefix="kb-")
        self.addCleanup(self.temporary.cleanup)
        self.vault = Path(self.temporary.name)
        self.root = self.vault / "knowledge-base" / "中文 A"
        self.template = self.vault / "knowledge-base-template" / "llm-wiki"
        shutil.copytree(REPO / "knowledge-base-template" / "llm-wiki", self.template)
        shutil.copytree(self.template, self.root)
        bind_overview(KnowledgeBase.load(self.root), self.vault)

    def findings(self):
        return inspect(self.root, self.vault)

    def codes(self):
        return {item.code for item in self.findings()}

    def populate(self, body="样本数量为 42K。", raw="样本数量为 42K。"):
        put(self.root / "raw" / "原始 资料.md", "# 原始资料\n\n" + raw)
        note(self.root / "wiki" / "概念.md", "# 概念\n\n" + body + "\n\n[原文](../raw/" + quote("原始 资料.md") + ")\n")
        note(self.root / "wiki" / "overview.md", "# 综述\n\n[概念](概念.md)\n", type="overview")
        self.index()

    def index(self):
        rows = ["# 知识索引", "", "| 页面 | 摘要 | Updated |", "| --- | --- | --- |"]
        for path in sorted((self.root / "wiki").rglob("*.md")):
            if path.name in {"index.md", "log.md"}:
                continue
            metadata = read_note(path).metadata
            if metadata.get("managed_by") != "agent":
                continue
            value = metadata.get("archived") if metadata.get("type") == "archive" else metadata.get("updated")
            rows.append(f"| [{path.stem}]({quote(path.relative_to(self.root / 'wiki').as_posix())}) | 摘要 | {value} |")
        put(self.root / "wiki" / "index.md", "\n".join(rows) + "\n")

    def test_empty_template_and_manual_copy(self):
        self.assertEqual(self.findings(), [])
        put(self.root / "README.md", "# 人工复制的库\n\n手工填写简介。\n")
        result = subprocess.run(["git", "init", "--initial-branch=main", str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / ".git").is_dir())
        self.assertEqual(self.findings(), [])

    def test_initialize_unicode_spaces_and_no_overwrite(self):
        target = initialize(self.vault, "新建 中文 库", "手工思考与可靠资料")
        self.assertIn("手工思考与可靠资料", (target / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((target / ".git").is_dir())
        self.assertFalse((target / ".obsidian").exists())
        original = (target / "README.md").read_bytes()
        with self.assertRaises(FileExistsError):
            initialize(self.vault, "新建 中文 库", "different")
        self.assertEqual(original, (target / "README.md").read_bytes())
        self.assertEqual(inspect(target, self.vault), [])
        base = yaml.safe_load((target / "knowledge.base").read_text(encoding="utf-8"))
        self.assertIn('this.file.path.startsWith("knowledge-base/新建 中文 库/")', base["filters"]["and"])

    def test_manual_overview_binding_and_unfilled_instance(self):
        base = self.root / "knowledge.base"
        shutil.copyfile(self.template / "knowledge.base", base)
        self.assertIn("base-binding-missing", self.codes())
        text = base.read_text(encoding="utf-8")
        for token, value in {"__KB_ROOT__": "knowledge-base/中文 A", "__WIKI_PATH__": "knowledge-base/中文 A/wiki", "__NOTES_PATH__": "knowledge-base/中文 A/Notes"}.items():
            text = text.replace(token, value)
        put(base, text)
        self.assertEqual(self.findings(), [])

    def test_initialize_rejects_content_before_creating_destination(self):
        isolated = self.vault / "initializer"
        template = isolated / "knowledge-base-template/llm-wiki"
        shutil.copytree(self.template, template)
        for relative in ("raw/private.md", "Clippings/assets/image.png", "Notes/idea.md", "reports/report.md", "wiki/article.md", "private.txt", "extra/data.pdf"):
            with self.subTest(path=relative):
                misplaced = template / relative
                put(misplaced, "synthetic private content")
                with self.assertRaisesRegex(ValueError, re.escape(relative)):
                    initialize(isolated, "新库", "description")
                self.assertFalse((isolated / "knowledge-base").exists())
                self.assertEqual(misplaced.read_text(encoding="utf-8"), "synthetic private content")
                misplaced.unlink()

    def test_initialize_checks_mapped_content_and_allows_new_templates(self):
        config = self.template / "kb.toml"
        text = config.read_text(encoding="utf-8").replace('"raw"', '"资料"').replace('"wiki"', '"编译/知识"').replace('"wiki/', '"编译/知识/')
        put(config, text)
        (self.template / "raw").rename(self.template / "资料")
        (self.template / "编译").mkdir()
        (self.template / "wiki").rename(self.template / "编译/知识")
        misplaced = self.template / "资料/private.md"
        put(misplaced, "synthetic")
        with self.assertRaisesRegex(ValueError, "资料/private.md"):
            initialize(self.vault, "映射库", "description")
        self.assertFalse((self.vault / "knowledge-base/映射库").exists())
        misplaced.unlink()
        put(self.template / "templates/extra/note.md", "# {{title}}")
        target = initialize(self.vault, "映射库", "description")
        self.assertEqual((target / "templates/extra/note.md").read_text(encoding="utf-8"), "# {{title}}")
        self.assertEqual(inspect(target, self.vault), [])

    def test_binding_escapes_expression_and_yaml_quotes(self):
        target = initialize(self.vault, "中文 O'Brien", "引用路径")
        kb = KnowledgeBase.load(target)
        # Exercise a quoted mapping without creating an OS-invalid Windows name.
        kb.paths["wiki"] = target / '知识 "引号"'
        shutil.copyfile(self.template / "knowledge.base", target / "knowledge.base")
        bind_overview(kb, self.vault)
        base = yaml.safe_load((target / "knowledge.base").read_text(encoding="utf-8"))
        expected = json.dumps('knowledge-base/中文 O\'Brien/知识 "引号"', ensure_ascii=False)
        self.assertIn(f"file.inFolder({expected})", base["views"][0]["filters"]["and"])

    def test_base_yaml_and_outer_shapes_are_checked(self):
        target = self.root / "wiki/bases/check.base"
        for content in ("filters: [", "- item\n", "scalar\n", "views: {}\n", "views: [1]\n",
                        "filters: []\n", "views:\n  - filters: 1\n", "filters: 1\n"):
            with self.subTest(content=content):
                put(target, content)
                self.assertTrue(any(item.code == "invalid-base" and item.level == "error" for item in self.findings()))
        put(target, 'filters: file.hasTag("example")\nviews:\n  - type: plugin-view\n    filters:\n      and:\n        - file.ext == "md"\n    plugin_settings:\n      1: [1, 2]\n')
        self.assertEqual(self.findings(), [])
        put(target, "")
        self.assertEqual(self.findings(), [])

    def test_base_samples_are_parsed_but_sources_are_not(self):
        put(self.root / "templates/broken.base", "filters: [")
        self.assertIn("invalid-base", self.codes())
        (self.root / "templates/broken.base").unlink()
        for name in ("raw/original.base", "Clippings/original.base"):
            put(self.root / name, "filters: [ __KB_ROOT__")
        self.assertNotIn("invalid-base", self.codes())
        self.assertNotIn("base-binding-missing", self.codes())

    def test_unmapped_clippings_are_reported_once_without_reclassifying_sources(self):
        config = self.root / "kb.toml"
        put(config, config.read_text(encoding="utf-8").replace('clippings = "Clippings"\n', ''))
        self.assertEqual(self.findings(), [])  # An unused placeholder is compatible.
        files = {"Clippings/one.md": "---\nbad: [\n---\noriginal", "Clippings/two.md": "# Original", "Clippings/bad.base": "filters: ["}
        for name, content in files.items():
            put(self.root / name, content)
        findings = self.findings()
        self.assertEqual([(item.level, item.code, item.path) for item in findings], [("review", "clippings-unmapped", self.root / "Clippings")])
        self.assertEqual(files, {name: (self.root / name).read_text(encoding="utf-8") for name in files})
        note(self.root / "wiki/概念.md", "# 知识", sources=["../Clippings/two.md"])
        self.index()
        self.assertIn("source-scope", self.codes())

    def test_clippings_used_by_another_mapping_are_not_inferred_as_sources(self):
        config = self.root / "kb.toml"
        text = config.read_text(encoding="utf-8").replace('clippings = "Clippings"\n', '').replace('reports = "reports"', 'reports = "Clippings/reports"')
        put(config, text)
        put(self.root / "Clippings/reports/result.md", "# Report\n")
        self.assertEqual(self.findings(), [])

    def test_all_six_page_templates_can_form_a_valid_library(self):
        self.populate()
        templates = sorted((self.root / "templates").glob("*.md"))
        self.assertEqual(len(templates), 6)
        for template in templates:
            body = template.read_text(encoding="utf-8").replace("{{date:YYYY-MM-DD}}", "2026-11-16").replace("{{title}}", template.stem)
            body = body.replace("__BASE_PATH__", "knowledge-base/中文 A/wiki/bases/分类.base")
            destination = self.root / ("raw/原始 资料.md" if template.stem == "新来源模板" else "Notes/想法.md" if template.stem == "人工笔记模板" else "wiki/" + template.name)
            put(destination, body)
            original = read_note(destination)
            data = dict(original.metadata)
            if data.get("type") == "raw":
                body += "\n样本数量为 42K。\n"
            else:
                if data.get("type") == "archive":
                    data["sources"] = ["./概念.md"]
                elif data.get("type") not in {"note", "category"}:
                    data["sources"] = ["../raw/原始 资料.md"]
                if data.get("type") != "category":
                    data["categories"] = ["[[knowledge-base/中文 A/wiki/分类入口模板]]"]
                body = "---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False) + "---\n" + original.body
            put(destination, body)
        category = (self.root / "templates/Bases/分类专用模板.base").read_text(encoding="utf-8")
        for token, value in {"__KB_ROOT__": "knowledge-base/中文 A", "__WIKI_DIR__": "wiki", "__TEMPLATES_DIR__": "templates", "__CATEGORY_PATH__": "knowledge-base/中文 A/wiki/分类入口模板"}.items():
            category = category.replace(token, value)
        put(self.root / "wiki/bases/分类.base", category)
        self.index()
        self.assertEqual(self.findings(), [])
        page = self.root / "wiki/知识页面模板.md"
        put(page, page.read_text(encoding="utf-8").replace("categories:\n- '[[knowledge-base/中文 A/wiki/分类入口模板]]'", "categories:\n- [[knowledge-base/中文 A/wiki/分类入口模板]]"))
        self.assertIn("property-type", self.codes())

    def test_init_rejects_escape_and_windows_special_names(self):
        for name in ("../outside", "a/b", "a\\b", "C:\\outside", "CON", "nul.txt", " name", "name.", ".git"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                initialize(self.vault, name, "description")

    def test_mapped_nested_layout(self):
        config = self.root / "kb.toml"
        text = config.read_text(encoding="utf-8").replace('"raw"', '"资料"').replace('"wiki"', '"编译/知识"').replace('"wiki/', '"编译/知识/')
        put(config, text)
        (self.root / "raw").rename(self.root / "资料")
        (self.root / "编译").mkdir()
        (self.root / "wiki").rename(self.root / "编译" / "知识")
        self.assertEqual(self.findings(), [])

    def test_mapping_escape_and_overlap_are_rejected(self):
        path = self.root / "kb.toml"
        original = path.read_text(encoding="utf-8")
        for replacement in ('"../other"', '"wiki"', '"wiki/raw"', '"."', '"C:/outside"', '"C:outside"', '"//server/share"'):
            put(path, original.replace('raw = "raw"', 'raw = ' + replacement))
            with self.subTest(replacement=replacement), self.assertRaises(ConfigError):
                KnowledgeBase.load(self.root)

    def test_mapping_requires_toml_table(self):
        put(self.root / "kb.toml", 'version = 1\npaths = ["raw", "wiki", "reports", "templates", "index", "log", "overview"]\n')
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(check_main([str(self.root)]), 2)

    def test_faithful_content_is_read_only(self):
        self.populate()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(self.findings(), [])
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_fake_value_is_review_not_a_factual_verdict(self):
        self.populate(body="样本数量为 99K。")
        matches = [item for item in self.findings() if item.code == "evidence-candidate"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].level, "review")
        self.assertIn("99K", matches[0].message)

    def test_source_title_with_hash_is_a_literal_path(self):
        self.populate()
        old = self.root / "raw" / "原始 资料.md"
        target = old.with_name("C# 原始资料.md")
        old.rename(target)
        for page in (self.root / "wiki" / "概念.md", self.root / "wiki" / "overview.md"):
            text = page.read_text(encoding="utf-8")
            text = text.replace("../raw/原始 资料.md", "../raw/" + target.name)
            text = text.replace(quote(old.name), quote(target.name))
            put(page, text)
        self.assertEqual(self.findings(), [])

    def test_raw_metadata_is_not_evidence(self):
        self.populate(body="数据收集始于 2026-11-16。", raw="无日期说明。")
        put(self.root / "raw" / "原始 资料.md", "---\ncollected: 2026-11-16\n---\n# 原件\n\n无日期说明。")
        self.assertIn("evidence-candidate", self.codes())

    def test_old_raw_bookkeeping_is_not_evidence(self):
        self.populate(body="数据始于 2026-11-16。", raw="无日期。")
        put(self.root / "raw" / "原始 资料.md", "# 原件\n\n> Source: example\n> Collected: 2026-11-16\n\n无日期。")
        self.assertIn("evidence-candidate", self.codes())

    def test_code_examples_are_not_links_or_evidence(self):
        self.populate(body='`[例子](missing.md)`\n\n~~~md\n数据 99999，[[不存在]]\n~~~\n')
        self.assertEqual(self.findings(), [])

    def test_duplicate_and_wrong_type_frontmatter(self):
        self.populate()
        target = self.root / "wiki" / "概念.md"
        put(target, "---\ntype: concept\ntype: archive\n---\n# Test\n")
        self.assertIn("invalid-metadata", self.codes())
        put(target, "---\ntype: [concept]\nmanaged_by: agent\n---\n# Test\n")
        self.assertIn("page-type", self.codes())

    def test_source_escape_does_not_read_other_library(self):
        self.populate()
        other = self.vault / "knowledge-base" / "B" / "raw" / "原始 资料.md"
        put(other, "只有另一个库包含 99K。")
        note(self.root / "wiki" / "概念.md", "# 概念\n\n99K", sources=["../../B/raw/原始 资料.md"])
        self.assertIn("source-scope", self.codes())

    def test_same_named_other_library_does_not_satisfy_link(self):
        self.populate()
        put(self.vault / "knowledge-base" / "B" / "wiki" / "其他.md", "# 其他\n")
        path = self.root / "wiki" / "概念.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n[其他](其他.md)\n")
        self.assertIn("broken-link", self.codes())

    def test_full_wikilink_stays_in_selected_library(self):
        self.populate()
        target = self.root / "wiki" / "概念.md"
        original = target.read_text(encoding="utf-8")
        put(target, original + "\n[[knowledge-base/中文 A/wiki/overview]]\n")
        self.assertEqual(self.findings(), [])
        put(target, original + "\n[[knowledge-base/B/wiki/overview]]\n")
        self.assertIn("cross-kb-link", self.codes())

    def test_intentional_human_link_allowed_generated_link_rejected(self):
        self.populate()
        note(self.root / "Notes" / "想法.md", "# 想法\n\n[[尚未想清楚]]\n", type="note", managed_by="human", sources=[])
        self.assertTrue(any(item.code == "broken-link" and item.level == "review" for item in self.findings()))
        with (self.root / "wiki" / "概念.md").open("a", encoding="utf-8") as stream:
            stream.write("\n[[尚未想清楚]]\n")
        self.assertIn("ambiguous-wikilink", self.codes())

    def test_no_material_handles_spaced_paths_and_ignores_fake_record(self):
        raw = self.root / "raw" / "没有 新内容.md"
        put(raw, "# 重复资料\n")
        self.assertIn("unprocessed-raw", self.codes())
        entry = "## [2026-11-16] ingest | 重复资料\n- Disposition: No material\n- Raw: [原文](../raw/" + quote(raw.name) + ")\n"
        put(self.root / "wiki" / "log.md", "# 日志\n\n```md\n" + entry + "```\n")
        self.assertIn("unprocessed-raw", self.codes())
        put(self.root / "wiki" / "log.md", "# 日志\n\n" + entry)
        self.assertNotIn("unprocessed-raw", self.codes())

    def test_pdf_evidence_reports_unverified(self):
        self.populate()
        put(self.root / "raw" / "paper.pdf", "synthetic test placeholder")
        note(self.root / "wiki" / "概念.md", "# 概念\n", sources=["../raw/paper.pdf"])
        self.assertIn("evidence-unverified", self.codes())

    def test_saved_analysis_and_frozen_archive(self):
        self.populate()
        note(self.root / "wiki" / "分析.md", "# 分析\n\n样本数量为 42K。", type="analysis")
        snapshot = self.root / "wiki" / "快照.md"
        note(snapshot, "# 快照\n\n归档当时的回答。", type="archive", archived="2026-11-15", sources=["概念.md"])
        self.index()
        before = snapshot.read_bytes()
        self.assertIn("archive-stale", self.codes())
        self.assertEqual(snapshot.read_bytes(), before)
        self.assertNotIn("source-scope", self.codes())

    def test_index_dates_are_optional_and_legacy_dates_are_ignored(self):
        self.populate()
        index = self.root / "wiki" / "index.md"
        original = index.read_text(encoding="utf-8")
        put(index, original.replace("2026-11-16", "2026-11-14"))
        self.assertEqual(self.findings(), [])
        put(index, "# 索引\n\n| 页面 | 摘要 |\n| --- | --- |\n| [概念](./概念.md) | 概念摘要 |\n| [综述](./overview.md) | 综述摘要 |\n")
        self.assertEqual(self.findings(), [])

    def test_index_still_rejects_missing_duplicate_and_broken_entries(self):
        self.populate()
        index = self.root / "wiki" / "index.md"
        put(index, "# 索引\n")
        self.assertIn("index-missing", self.codes())
        put(index, "# 索引\n\n[概念](./概念.md)\n[重复](./概念.md)\n[缺失](./missing.md)\n")
        self.assertTrue({"index-duplicate", "broken-link", "index-missing"} <= self.codes())

    def test_human_organization_boundary(self):
        # The Agent performs this workflow; no automatic content rewriting API.
        misplaced = self.root / "随手记录.md"
        put(misplaced, "---\ncustom: 保留\ncreated: 2026-01-02\n---\n\n# 想法\n\n我倾向于先观察，而不是急于判断。\n")
        original = read_note(misplaced)
        raw = self.root / "raw" / "原件.md"
        put(raw, "# 原件\n\n不能移动或补属性。")
        raw_bytes = raw.read_bytes()
        referring = self.root / "Notes" / "关联笔记.md"
        note(referring, "# 关联笔记\n\n[个人观点](../随手记录.md)\n", type="note", managed_by="human", sources=[])
        self.assertIn("human-location", self.codes())
        destination = self.root / "Notes" / misplaced.name
        misplaced.rename(destination)
        self.assertIn("broken-link", self.codes())
        put(referring, referring.read_text(encoding="utf-8").replace("(../随手记录.md)", "(随手记录.md)"))
        data = dict(original.metadata)
        for key, value in {"type": "note", "managed_by": "human", "categories": [], "tags": [], "aliases": []}.items():
            data.setdefault(key, value)
        put(destination, "---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False) + "---\n" + original.body)
        after = read_note(destination)
        self.assertEqual(after.body, original.body)
        self.assertEqual(after.metadata["custom"], original.metadata["custom"])
        self.assertEqual(after.metadata["created"], original.metadata["created"])
        self.assertEqual(raw.read_bytes(), raw_bytes)
        self.assertNotIn("human-location", self.codes())
        self.assertNotIn("broken-link", self.codes())

    def test_cli_exit_codes(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(check_main([str(self.root)]), 0)
            put(self.root / "raw" / "new.md", "# New\n")
            self.assertEqual(check_main([str(self.root)]), 1)
            self.assertEqual(check_main([str(self.root / "missing")]), 2)

    def test_clippings_are_immutable_sources_and_support_no_material(self):
        clip = self.root / "Clippings" / "网页 文章.md"
        put(clip, "---\nsource: https://example.org/article\nclipped: 2026-11-16\n---\n# 原文\n\n样本为 42K。\n")
        before = clip.read_bytes()
        self.assertIn("unprocessed-raw", self.codes())
        self.assertNotIn("human-location", self.codes())
        self.assertNotIn("human-properties", self.codes())
        put(self.root / "wiki/log.md", "# 日志\n\n## [2026-11-16] ingest | 网页\n- Disposition: No material\n- Raw: [原文](../Clippings/" + quote(clip.name) + ")\n")
        self.assertEqual(self.findings(), [])
        note(self.root / "wiki/概念.md", "# 概念\n\n样本为 42K。", sources=["../Clippings/" + clip.name])
        note(self.root / "wiki/overview.md", "# 综述\n\n样本为 42K。", type="overview", sources=["../Clippings/" + clip.name])
        self.index()
        self.assertEqual(self.findings(), [])
        note(self.root / "wiki/概念.md", "# 概念\n\n日期为 2026-11-16，数量为 99K。", sources=["../Clippings/" + clip.name])
        self.assertIn("evidence-candidate", self.codes())
        self.assertEqual(clip.read_bytes(), before)

    def test_optional_clippings_mapping_and_custom_directory(self):
        config = self.root / "kb.toml"
        original = config.read_text(encoding="utf-8")
        put(config, original.replace('clippings = "Clippings"\n', ''))
        (self.root / "Clippings/.gitkeep").unlink()
        (self.root / "Clippings").rmdir()
        self.assertEqual(self.findings(), [])
        put(config, original.replace('clippings = "Clippings"', 'clippings = "网页剪藏"'))
        self.assertIn("directory-missing", self.codes())
        put(self.root / "网页剪藏/new.md", "# New\n")
        self.assertIn("unprocessed-raw", self.codes())
        self.assertNotIn("human-location", self.codes())

    def test_clippings_mapping_rejects_escape_and_overlap(self):
        path = self.root / "kb.toml"
        original = path.read_text(encoding="utf-8")
        for replacement in ("../other", "raw", "Notes", "wiki/clips"):
            put(path, original.replace('clippings = "Clippings"', 'clippings = "' + replacement + '"'))
            with self.subTest(replacement=replacement), self.assertRaises(ConfigError):
                KnowledgeBase.load(self.root)

    def test_clippings_cannot_supply_cross_library_evidence(self):
        other = self.vault / "knowledge-base/B/Clippings/article.md"
        put(other, "# 外库原文\n\n99K\n")
        note(self.root / "wiki/概念.md", "# 概念\n\n99K", sources=["../../B/Clippings/article.md"])
        self.assertIn("source-scope", self.codes())
        put(self.root / "wiki/log.md", "# 日志\n\n## [2026-11-16] ingest | 网页\n- Disposition: No material\n- Raw: [外库](../../B/Clippings/article.md)\n")
        self.assertIn("log-raw-invalid", self.codes())


    def test_walk_read_error_is_runtime_failure(self):
        blocked = self.root / "raw/unreadable"
        put(blocked / "source.md", "# source\n")
        real_scandir = os.scandir

        def denied(path):
            if Path(path).resolve() == blocked.resolve():
                raise PermissionError(13, "synthetic permission denial", str(path))
            return real_scandir(path)

        error = io.StringIO()
        with patch("kb_common.os.scandir", side_effect=denied), redirect_stderr(error):
            self.assertEqual(check_main([str(self.root)]), 2)
        self.assertIn("unreadable", error.getvalue())
        self.assertIn("unprocessed-raw", self.codes())

    def test_human_missing_links_are_review_and_short_links_grouped_per_page(self):
        self.populate()
        human = self.root / "Notes/human.md"
        note(human, "[pending](./pending.md)\n[[pending]] [[概念]] [[概念]]\n"
             "[[knowledge-base/中文 A/Notes/missing]]", type="note", managed_by="human", sources=[])
        findings = [item for item in self.findings() if item.path == human]
        self.assertTrue(all(item.level == "review" for item in findings))
        self.assertEqual(sum(item.code == "broken-link" for item in findings), 3)
        self.assertEqual(sum(item.code == "human-wikilink-scope" for item in findings), 1)

    def test_reports_and_log_links_are_strict_without_article_metadata(self):
        put(self.root / "reports/review.md", "[missing](../wiki/missing.md)\n")
        put(self.root / "wiki/log.md", "# Log\n[report](../reports/missing.md)\n")
        found = self.findings()
        self.assertEqual(sum(item.code == "broken-link" and item.level == "error" for item in found), 2)
        self.assertFalse(any(item.code in {"human-properties", "sources-missing"} for item in found))

    def test_dot_title_exact_file_then_appended_md(self):
        self.populate()
        put(self.root / "raw/方法 v1.0.md", "# 原文\n")
        target = self.root / "wiki/概念.md"
        note(target, "[方法](../raw/方法%20v1.0)\n[[knowledge-base/中文 A/raw/方法 v1.0]]")
        self.assertNotIn("broken-link", self.codes())
        # An exact file takes priority over its Markdown namesake.
        put(self.root / "raw/方法 v1.0", "exact")
        note(target, "[方法](../raw/方法%20v1.0#not-a-heading)")
        self.assertNotIn("broken-fragment", self.codes())

    def test_reference_links_shared_across_index_log_reports_and_evidence(self):
        self.populate()
        note(self.root / "wiki/概念.md", "样本 [42K][ Data ]。\n\n[Data]: ../raw/原始%20资料.md\n")
        put(self.root / "wiki/index.md", "| [概念][c] | 摘要 | 2026-11-16 |\n"
            "| [综述][o] | 摘要 | 2026-11-16 |\n\n[c]: ./概念.md\n[o]: ./overview.md\n")
        put(self.root / "raw/重复.md", "# 重复资料\n")
        put(self.root / "wiki/log.md", "## [2026-11-16] ingest | 重复\n- Disposition: No material\n"
            "- Raw: [重复][]\n\n[重复]: ../raw/重复.md\n")
        put(self.root / "reports/review.md", "[概念][c]\n\n[c]: ../wiki/概念.md\n")
        self.assertEqual(self.findings(), [])


    def prepare_snapshot(self):
        self.populate()
        original = self.root / "Notes/原笔记.md"
        note(original, "# 原笔记\n样本数量为 42K。", type="note", managed_by="human", sources=[])
        raw = self.root / "raw/原始 资料.md"
        metadata = {"snapshot_source_note": "../Notes/原笔记.md", "snapshot_source_mtime_ns": str(original.stat().st_mtime_ns)}
        put(raw, "---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n样本数量为 42K。\n")
        return original, raw, metadata

    def test_snapshot_mtime_warning_grouped_and_read_only(self):
        original, raw, metadata = self.prepare_snapshot()
        self.assertEqual(self.findings(), [])
        second = raw.with_name("第二份快照.md")
        second.write_bytes(raw.read_bytes())
        note(self.root / "wiki/第二知识.md", "样本数量为 42K。", sources=["../raw/第二份快照.md"])
        self.index()
        before = {path: path.read_bytes() for path in (raw, second, self.root / "wiki/概念.md", self.root / "wiki/第二知识.md")}
        current = original.stat()
        os.utime(original, ns=(current.st_atime_ns, current.st_mtime_ns + 2_000_000_000))
        found = [item for item in self.findings() if item.code.startswith("snapshot-")]
        self.assertEqual([(item.code, item.level, item.path) for item in found], [("snapshot-source-changed", "review", original)])
        self.assertIn("第二份快照.md", found[0].message)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_snapshot_missing_invalid_and_legacy_metadata(self):
        original, raw, metadata = self.prepare_snapshot()
        original.unlink()
        self.assertIn("snapshot-source-missing", self.codes())
        for changes in ({"snapshot_source_mtime_ns": 123}, {"snapshot_source_mtime_ns": "1.25"}, {"snapshot_source_note": None}, {"snapshot_source_mtime_ns": None}):
            with self.subTest(changes=changes):
                put(raw, "---\n" + yaml.safe_dump(metadata | changes, allow_unicode=True) + "---\n样本数量为 42K。")
                self.assertIn("snapshot-metadata", self.codes())
        put(raw, "# 旧快照\n样本数量为 42K。")
        self.assertEqual(self.findings(), [])

    def test_snapshot_scope_is_checked_before_original_status(self):
        original, raw, metadata = self.prepare_snapshot()
        for source in ("../../B/Notes/private.md", "../wiki/概念.md", "C:/private.md", "https://example.org/note"):
            with self.subTest(source=source):
                snapshot = read_note(raw)
                snapshot.metadata["snapshot_source_note"] = source
                found = []
                # Resolution may inspect path components, but the source itself must
                # never be opened or stat'ed by the snapshot comparison branch.
                with patch("check_kb.read_note", side_effect=AssertionError("unexpected source read")):
                    inspect_snapshots(KnowledgeBase.load(self.root), {raw: snapshot}, lambda *item: found.append(item))
                self.assertEqual([item[1] for item in found], ["snapshot-source-scope"])

    def test_snapshot_unreferenced_and_archive_only_sources_not_compared(self):
        original, raw, metadata = self.prepare_snapshot()
        metadata["snapshot_source_mtime_ns"] = "0"
        put(self.root / "raw/未引用快照.md", "---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n原文")
        note(self.root / "wiki/归档.md", "历史回答", type="archive", archived="2026-11-16", sources=["./概念.md"])
        self.index()
        self.assertNotIn("snapshot-source-changed", self.codes())

    def test_snapshot_original_status_failure_is_review(self):
        original, raw, _ = self.prepare_snapshot()
        snapshot = read_note(raw)
        kb = KnowledgeBase.load(self.root)
        real_stat = Path.stat

        def denied(path, *args, **kwargs):
            if path == original:
                raise PermissionError("synthetic original-note status denial")
            return real_stat(path, *args, **kwargs)

        found = []
        with patch.object(Path, "stat", denied):
            inspect_snapshots(kb, {raw: snapshot}, lambda *item: found.append(item))
        self.assertEqual([(item[0], item[1]) for item in found], [("review", "snapshot-source-unverified")])


class LiteralBoundaryTests(unittest.TestCase):
    def test_reference_labels_images_and_first_definition(self):
        parsed = parse_markdown('[Text][ A  B ] ![Image][] [Straße][STRASSE]\n\n'
                                '[a b]: <./first file.md> "title"\n[a B]: ./wrong.md\n'
                                '[image]: ./image.png\n[straße]: ./unicode.md\n')
        self.assertEqual([link.target for link in parsed.links], ["./first file.md", "./image.png", "./unicode.md"])
        self.assertIn("Text Image Straße", parsed.visible())

    def test_reference_paths_not_evidence_but_display_text_is(self):
        body = '[42K][r] ![2026-11-17][img]\n\n[r]: https://example.org/99999 "3.14"\n[img]: ./88888.png\n'
        self.assertEqual({item.value for item in candidates(body)}, {"42K", "2026-11-17"})
        self.assertEqual(parse_markdown('```md\n[ghost]: ./missing.md\n```\n[display][ghost]').links, ())

    def test_candidates_do_not_match_larger_values(self):
        for body, source in (("42K", "142K"), ("3.14", "3.1415"), ("2026-11", "2026-11-16")):
            with self.subTest(body=body):
                self.assertFalse(contains(source, candidates(body)[0]))

    def test_small_plain_numbers_require_semantic_review(self):
        self.assertEqual(candidates("样本 42 个，另有 500 个。"), [])

    def test_multiline_direct_quote(self):
        body = '> A sufficiently long direct\n> quotation preserved from the source.'
        found = candidates(body)
        self.assertEqual(len(found), 1)
        self.assertTrue(contains("A sufficiently long direct quotation preserved from the source.", found[0]))


if __name__ == "__main__":
    unittest.main()
