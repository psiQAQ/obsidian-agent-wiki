"""Read-only structure, link and bounded evidence checks for one knowledge base."""

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PureWindowsPath
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

from evidence import candidates, contains, prose, source_body
from kb_common import ConfigError, DIRECTORIES, KnowledgeBase, Note, REPO_ROOT, SPECIAL_FILES, files_under, read_note, within
from markdown_links import WIKI_LINK, parse_markdown


KINDS = {"source", "entity", "concept", "analysis", "archive", "overview", "category"}
ADMIN_TYPES = {"index", "log", "report", "document", "dashboard"}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: Path
    message: str


def day(value):
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


def file_target(target, known):
    # Titles may contain dots; append .md rather than replacing a suffix.
    markdown = target.with_name(target.name + ".md")
    return markdown if target not in known and markdown in known else target


def local_target(path, link, known):
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        return None, ""
    target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
    return file_target(target, known), unquote(parsed.fragment)


def has_fragment(path, fragment):
    if not fragment:
        return True
    if path.suffix.lower() != ".md":
        return True  # PDF pages and application-specific embeds need UI verification.
    body = prose(read_note(path).body)
    if fragment.startswith("^"):
        return re.search(r"\^" + re.escape(fragment[1:]) + r"(?:\s|$)", body) is not None
    headings = [re.sub(r"\s+#+\s*$", "", match[1]).strip() for match in re.finditer(r"^#{1,6}\s+(.+)$", body, re.M)]
    requested = fragment.split("#")[-1].casefold()
    return any(requested in {heading.casefold(), re.sub(r"[^\w\- ]", "", heading.casefold()).replace(" ", "-")} for heading in headings)


def inspect_snapshots(kb, snapshots, report):
    """Compare metadata only; never refresh snapshots or read the original body."""
    grouped = {}
    for snapshot, note in snapshots.items():
        data = note.metadata
        keys = ("snapshot_source_note", "snapshot_source_mtime_ns")
        if not any(key in data for key in keys):
            continue  # Older sources remain compatible without retroactive edits.
        source, mtime = (data.get(key) for key in keys)
        if not isinstance(source, str) or not source or not isinstance(mtime, str) or not re.fullmatch(r"[0-9]+", mtime):
            report("review", "snapshot-metadata", snapshot, "snapshot requires source path and quoted decimal snapshot_source_mtime_ns; metadata is incomplete or invalid")
            continue
        if "\\" in source or Path(source).is_absolute() or PureWindowsPath(source).drive or urlsplit(source).scheme:
            report("review", "snapshot-source-scope", snapshot, "snapshot_source_note must be a relative path into this library's Notes; not followed")
            continue
        original = (snapshot.parent / source).resolve()
        if not within(original, kb.paths["notes"]):
            report("review", "snapshot-source-scope", snapshot, "original is outside this library's Notes; not followed: " + source)
            continue
        grouped.setdefault(original, []).append((snapshot, mtime.lstrip("0") or "0"))
    for original, entries in grouped.items():
        labels = ", ".join(path.relative_to(kb.root).as_posix() for path, _ in entries)
        try:
            current = original.stat()
            if not original.is_file():
                report("review", "snapshot-source-unverified", original, "original is not a file; referenced snapshots: " + labels)
            elif any(str(current.st_mtime_ns) != mtime for _, mtime in entries):
                report("review", "snapshot-source-changed", original, "original may have changed; review whether to ingest again (mtime is not content proof); referenced snapshots: " + labels)
        except FileNotFoundError:
            report("review", "snapshot-source-missing", original, "original note is missing; referenced snapshots: " + labels)
        except OSError as error:
            report("review", "snapshot-source-unverified", original, f"cannot verify original note: {error}; referenced snapshots: {labels}")


def inspect(root: Path, vault: Path = REPO_ROOT) -> list[Finding]:
    kb = KnowledgeBase.load(root)
    findings = []

    def report(level, code, path, message):
        findings.append(Finding(level, code, path, message))

    for key in (*DIRECTORIES, "notes", *(("clippings",) if "clippings" in kb.paths else ())):
        if not kb.paths[key].is_dir():
            report("error", "directory-missing", kb.paths[key], f"required {key} directory is missing")
    for key in SPECIAL_FILES:
        if not kb.paths[key].is_file():
            report("error", "special-file-missing", kb.paths[key], f"required {key} file is missing")
    all_files = list(files_under(kb.root))
    known = set(all_files)
    if kb.root != (vault / "knowledge-base-template/llm-wiki").resolve():
        for path in all_files:
            if path.suffix == ".base" and not within(path, kb.paths["templates"]):
                placeholders = sorted(set(re.findall(r"__(?:KB_ROOT|WIKI_PATH|NOTES_PATH|WIKI_DIR|TEMPLATES_DIR|CATEGORY_PATH)__", path.read_text(encoding="utf-8-sig"))))
                if placeholders:
                    report("error", "base-binding-missing", path, "fill Base bindings before use: " + ", ".join(placeholders))
    notes = {}
    excluded = [*kb.source_roots, kb.paths["templates"]]
    admin_files = {kb.root / name for name in ("README.md", "AGENTS.md", "LICENSES.md")}
    navigation_files = {kb.paths[key] for key in ("index", "log")}
    navigation_files.update(path for path in all_files if within(path, kb.paths["reports"]))
    for path in all_files:
        if path.suffix.lower() != ".md" or any(within(path, directory) for directory in excluded):
            continue
        try:
            notes[path] = read_note(path)
        except (ValueError, UnicodeError, yaml.YAMLError) as error:
            report("error", "invalid-metadata", path, str(error))

    articles = {}
    for path, note in notes.items():
        metadata = note.metadata
        if metadata.get("type") is not None and not isinstance(metadata["type"], str):
            report("error", "page-type", path, "type must be text")
            continue
        if metadata.get("managed_by") not in (None, "agent", "human"):
            report("error", "managed-by", path, "managed_by must be agent or human")
        if path in admin_files or path in navigation_files or metadata.get("type") in ADMIN_TYPES:
            continue
        owned = metadata.get("managed_by") == "agent"
        kind = metadata.get("type")
        if not owned:
            if not within(path, kb.paths["notes"]):
                report("review", "human-location", path, "protected content outside Notes; determine ownership and destination before organizing")
            missing = [key for key in ("type", "managed_by", "categories", "tags", "aliases", "created") if key not in metadata]
            if missing:
                report("review", "human-properties", path, "fill only missing properties without inventing values: " + ", ".join(missing))
        else:
            if not within(path, kb.paths["wiki"]):
                report("error", "generated-location", path, "Agent knowledge must be inside the configured wiki directory")
            if kind not in KINDS:
                report("error", "page-type", path, f"unknown Agent page type: {kind!r}")
            else:
                articles[path] = note
        for key in ("categories", "tags", "aliases", "sources"):
            if key not in metadata and not owned:
                continue
            value = metadata.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                report("error", "property-type", path, f"{key} must be a list of strings")
        for key in ("created", "updated", "archived"):
            if metadata.get(key) is not None and day(metadata[key]) is None:
                report("error", "date-format", path, f"{key} must be YYYY-MM-DD or empty")
        empty = kind == "overview" and metadata.get("status") == "empty"
        if owned and not empty:
            for key in (("created", "archived") if kind == "archive" else ("created", "updated")):
                if day(metadata.get(key)) is None:
                    report("error", "date-missing", path, f"generated page requires {key}")

    def check_link(path, target, fragment, owned):
        if not within(target, kb.root):
            report("error" if owned else "review", "cross-kb-link", path, "target outside selected knowledge base; not followed: " + str(target))
        elif not target.is_file():
            report("error" if owned else "review", "broken-link", path, "missing target (human content may intentionally link to a pending page): " + str(target.relative_to(kb.root)))
        else:
            try:
                if not has_fragment(target, fragment):
                    report("error" if owned else "review", "broken-fragment", path, f"missing heading/block: {fragment}")
            except (ValueError, UnicodeError, yaml.YAMLError) as error:
                report("review", "fragment-unverified", path, str(error))

    parsed_notes = {path: parse_markdown(note.body) for path, note in notes.items() if path not in admin_files}
    for path, parsed in parsed_notes.items():
        note = notes[path]
        if path in admin_files:
            continue
        owned = path in navigation_files or note.metadata.get("managed_by") == "agent"
        for link in parsed.links:
            target, fragment = local_target(path, link.target, known)
            if target is not None:
                check_link(path, target, fragment, owned)
        strings = [parsed.text]
        for value in note.metadata.values():
            strings.extend([value] if isinstance(value, str) else [item for item in value if isinstance(item, str)] if isinstance(value, list) else [])
        short_links = set()
        for match in WIKI_LINK.finditer("\n".join(strings)):
            destination = match[1].split("|")[0].replace("\\", "").strip()
            name, _, fragment = destination.partition("#")
            if not name:
                target = path
            elif "/" in name:
                target = file_target((vault / name).resolve(), known)
            else:
                if owned:
                    report("error", "ambiguous-wikilink", path, "generated wikilink needs a full vault-relative path: " + name)
                    continue
                short_links.add(name)
                matches = [candidate for candidate in all_files if candidate.name == name]
                if not matches:
                    matches = [candidate for candidate in all_files if candidate.name == name + ".md"]
                if not matches:
                    report("review", "broken-link", path, "missing local wikilink target; may be a pending page: " + name)
                    continue
                if len(matches) != 1:
                    report("review", "ambiguous-wikilink", path, "multiple local matches: " + name)
                    continue
                target = matches[0]
            check_link(path, target, fragment, owned)
        if short_links:
            report("review", "human-wikilink-scope", path, "short wikilinks have unverified actual Vault resolution; checked only this library: " + ", ".join(sorted(short_links)))

    raw_references = set()
    snapshots = {}
    for path, note in articles.items():
        metadata = note.metadata
        kind = metadata["type"]
        sources = metadata.get("sources")
        if not isinstance(sources, list) or any(not isinstance(value, str) for value in sources):
            continue
        if not sources and kind == "category":
            continue  # Navigation pages do not assert sourced knowledge.
        if not sources and kind == "overview" and metadata.get("status") == "empty":
            if len(articles) > 1:
                report("review", "empty-overview", path, "knowledge exists; review whether the initial overview should be populated")
            continue
        if not sources:
            report("error", "sources-missing", path, "generated knowledge requires evidence paths")
            continue
        allowed = (kb.paths["wiki"],) if kind == "archive" else kb.source_roots
        evidence = []
        for value in sources:
            if value.startswith("[[") or "\\" in value or Path(value).is_absolute() or urlsplit(value).scheme:
                report("error", "source-path", path, "sources must contain literal relative file paths: " + value)
                continue
            target = (path.parent / value).resolve()
            if not any(within(target, directory) for directory in allowed) or target == path:
                report("error", "source-scope", path, "source outside permitted evidence layer; not followed: " + value)
                continue
            if not target.is_file():
                report("error", "source-missing", path, "source does not exist: " + value)
                continue
            if kind == "archive":
                cited = notes.get(target)
                if cited is None or target not in articles:
                    report("error", "archive-source", path, "archive must cite knowledge articles: " + value)
                else:
                    updated, archived = day(cited.metadata.get("updated")), day(metadata.get("archived"))
                    if updated and archived and updated > archived:
                        report("review", "archive-stale", path, "cited page changed after archival; preserve the snapshot: " + value)
                continue
            raw_references.add(target)
            if target.suffix.lower() not in {".md", ".txt"}:
                report("review", "evidence-unverified", path, "non-text evidence needs separate reading: " + value)
                continue
            try:
                raw = read_note(target)
                if within(target, kb.paths["raw"]):
                    snapshots[target] = raw
                evidence.append(source_body(raw.body))
            except (ValueError, UnicodeError, yaml.YAMLError) as error:
                report("review", "evidence-unverified", path, f"cannot parse evidence {value}: {error}")
        if kind != "archive" and evidence:
            for candidate in candidates(note.body):
                if not any(contains(text, candidate) for text in evidence):
                    report("review", "evidence-candidate", path, f"{candidate.kind} not located verbatim; review context/derivation: {candidate.value}")

    inspect_snapshots(kb, snapshots, report)

    index_path = kb.paths["index"]
    if index_path in notes:
        indexed = {}
        parsed = parsed_notes[index_path]
        lines = parsed.text.splitlines()
        for link in parsed.links:
            target, _ = local_target(index_path, link.target, known)
            if target is None:
                continue
            if not within(target, kb.paths["wiki"]):
                report("error", "index-scope", index_path, "index target is outside the wiki: " + link.target)
            if target in indexed:
                report("error", "index-duplicate", index_path, "duplicate entry: " + link.target)
            date_match = re.search(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|?\s*$", lines[link.line - 1])
            indexed[target] = day(date_match[1]) if date_match else None
        for path, note in articles.items():
            if path == kb.paths["overview"] and note.metadata.get("status") == "empty":
                continue
            if path not in indexed:
                report("error", "index-missing", path, "knowledge page is absent from the index")
                continue
            field = "archived" if note.metadata.get("type") == "archive" else "updated"
            if day(note.metadata.get(field)) != indexed[path]:
                report("error", "index-date", path, "index date must equal page " + field)

    log_path = kb.paths["log"]
    no_material = set()
    if log_path in notes:
        parsed = parsed_notes[log_path]
        for match in re.finditer(r"^## \[.*?(?=^## \[|\Z)", parsed.text, re.M | re.S):
            record = match[0]
            if not re.match(r"^## \[\d{4}-\d{2}-\d{2}\]\s+ingest\s*\|", record):
                continue
            if not re.search(r"^- Disposition:\s*No material\s*$", record, re.M | re.I):
                continue
            start_line = parsed.text.count("\n", 0, match.start()) + 1
            raw_lines = {start_line + i for i, line in enumerate(record.splitlines()) if re.match(r"^- Raw:\s*", line)}
            links = [link.target for link in parsed.links if link.line in raw_lines]
            if not links:
                report("error", "log-raw-missing", log_path, "No material record requires a Raw Markdown link")
            for link in links:
                target, _ = local_target(log_path, link, known)
                if target is None or not any(within(target, directory) for directory in kb.source_roots) or not target.is_file():
                    report("error", "log-raw-invalid", log_path, "No material Raw must resolve inside a configured source directory: " + link)
                else:
                    no_material.add(target)
    for path in all_files:
        source_root = next((directory for directory in kb.source_roots if within(path, directory)), None)
        if source_root is not None and path.name != ".gitkeep" and "assets" not in path.relative_to(source_root).parts:
            if path not in raw_references and path not in no_material:
                report("review", "unprocessed-raw", path, "not referenced by compiled knowledge or a No material log entry")

    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="the explicitly selected knowledge-base root")
    args = parser.parse_args(argv)
    try:
        findings = inspect(args.root)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Check failed: {error}", file=sys.stderr)
        return 2
    root = args.root.resolve()
    for finding in findings:
        label = finding.path.relative_to(root) if within(finding.path, root) else finding.path
        print(f"[{finding.level.upper()}] {finding.code} | {label.as_posix()} | {finding.message}")
    errors = sum(item.level == "error" for item in findings)
    reviews = sum(item.level == "review" for item in findings)
    print(f"Summary: {errors} error(s), {reviews} review item(s). Read-only; semantic fact review is still required.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
