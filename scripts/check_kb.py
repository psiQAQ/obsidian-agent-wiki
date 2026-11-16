"""Read-only structure, link and bounded evidence checks for one knowledge base."""

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

from evidence import candidates, contains, prose, source_body
from kb_common import ConfigError, DIRECTORIES, KnowledgeBase, Note, REPO_ROOT, SPECIAL_FILES, files_under, read_note, within


MD_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^\s)]+)(?:\s+\"[^\"]*\")?\s*\)")
WIKI_LINK = re.compile(r"!?\[\[([^\]\n]+)\]\]")
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


def md_targets(body):
    text = re.sub(r"`[^`\n]*`", "", prose(body))
    return [match[1].strip("<>") for match in MD_LINK.finditer(text)]


def local_target(path, link):
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        return None, ""
    target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
    return target, unquote(parsed.fragment)


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


def inspect(root: Path, vault: Path = REPO_ROOT) -> list[Finding]:
    kb = KnowledgeBase.load(root)
    findings = []

    def report(level, code, path, message):
        findings.append(Finding(level, code, path, message))

    for key in (*DIRECTORIES, "notes"):
        if not kb.paths[key].is_dir():
            report("error", "directory-missing", kb.paths[key], f"required {key} directory is missing")
    for key in SPECIAL_FILES:
        if not kb.paths[key].is_file():
            report("error", "special-file-missing", kb.paths[key], f"required {key} file is missing")
    all_files = list(files_under(kb.root))
    known = set(all_files)
    notes = {}
    excluded = [kb.paths[key] for key in ("raw", "reports", "templates")]
    admin_files = {kb.root / name for name in ("README.md", "AGENTS.md", "LICENSES.md")}
    admin_files.update(kb.paths[key] for key in ("index", "log"))
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
        if path in admin_files or metadata.get("type") in ADMIN_TYPES:
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
            report("error", "broken-link", path, "missing target: " + str(target.relative_to(kb.root)))
        else:
            try:
                if not has_fragment(target, fragment):
                    report("error", "broken-fragment", path, f"missing heading/block: {fragment}")
            except (ValueError, UnicodeError, yaml.YAMLError) as error:
                report("review", "fragment-unverified", path, str(error))

    for path, note in notes.items():
        if path in admin_files:
            continue
        owned = note.metadata.get("managed_by") == "agent"
        for link in md_targets(note.body):
            target, fragment = local_target(path, link)
            if target is not None:
                check_link(path, target, fragment, owned)
        strings = [re.sub(r"`[^`\n]*`", "", prose(note.body))]
        for value in note.metadata.values():
            strings.extend([value] if isinstance(value, str) else [item for item in value if isinstance(item, str)] if isinstance(value, list) else [])
        for match in WIKI_LINK.finditer("\n".join(strings)):
            destination = match[1].split("|")[0].replace("\\", "").strip()
            name, _, fragment = destination.partition("#")
            if not name:
                target = path
            elif "/" in name:
                target = (vault / name).resolve()
                if not target.suffix:
                    target = target.with_suffix(".md")
            else:
                if owned:
                    report("error", "ambiguous-wikilink", path, "generated wikilink needs a full vault-relative path: " + name)
                    continue
                matches = [candidate for candidate in known if candidate.name == name or candidate.name == name + ".md"]
                if not matches:
                    continue  # Intentional unresolved links are allowed in human notes.
                if len(matches) != 1:
                    report("review", "ambiguous-wikilink", path, "multiple local matches: " + name)
                    continue
                target = matches[0]
            if not owned and within(target, kb.root) and not target.exists():
                continue
            check_link(path, target, fragment, owned)

    raw_references = set()
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
        allowed = kb.paths["wiki"] if kind == "archive" else kb.paths["raw"]
        evidence = []
        for value in sources:
            if value.startswith("[[") or "\\" in value or Path(value).is_absolute() or urlsplit(value).scheme:
                report("error", "source-path", path, "sources must contain literal relative file paths: " + value)
                continue
            target = (path.parent / value).resolve()
            if not within(target, allowed) or target == path:
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
                evidence.append(source_body(raw.body))
            except (ValueError, UnicodeError, yaml.YAMLError) as error:
                report("review", "evidence-unverified", path, f"cannot parse evidence {value}: {error}")
        if kind != "archive" and evidence:
            for candidate in candidates(note.body):
                if not any(contains(text, candidate) for text in evidence):
                    report("review", "evidence-candidate", path, f"{candidate.kind} not located verbatim; review context/derivation: {candidate.value}")

    index_path = kb.paths["index"]
    if index_path in notes:
        indexed = {}
        for line in prose(notes[index_path].body).splitlines():
            for link in md_targets(line):
                target, fragment = local_target(index_path, link)
                if target is None:
                    continue
                check_link(index_path, target, fragment, True)
                if not within(target, kb.paths["wiki"]):
                    report("error", "index-scope", index_path, "index target is outside the wiki: " + link)
                if target in indexed:
                    report("error", "index-duplicate", index_path, "duplicate entry: " + link)
                date_match = re.search(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|?\s*$", line)
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
        for record in re.split(r"(?=^## \[)", prose(notes[log_path].body), flags=re.M):
            if not re.match(r"^## \[\d{4}-\d{2}-\d{2}\]\s+ingest\s*\|", record):
                continue
            if not re.search(r"^- Disposition:\s*No material\s*$", record, re.M | re.I):
                continue
            raw_lines = re.findall(r"^- Raw:\s*(.+)$", record, re.M)
            links = [link for line in raw_lines for link in md_targets(line)]
            if not links:
                report("error", "log-raw-missing", log_path, "No material record requires a Raw Markdown link")
            for link in links:
                target, _ = local_target(log_path, link)
                if target is None or not within(target, kb.paths["raw"]) or not target.is_file():
                    report("error", "log-raw-invalid", log_path, "No material Raw must resolve inside raw: " + link)
                else:
                    no_material.add(target)
    for path in all_files:
        if within(path, kb.paths["raw"]) and path.name != ".gitkeep" and "assets" not in path.relative_to(kb.paths["raw"]).parts:
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
