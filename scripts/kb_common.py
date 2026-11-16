"""Knowledge-base paths and YAML boundary parsing. No writes on import."""

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DIRECTORIES = ("raw", "wiki", "reports", "templates")
SPECIAL_FILES = ("index", "log", "overview")
SKIP_DIRECTORIES = {".git", ".obsidian", ".cache", ".venv", "__pycache__"}


class ConfigError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than silently discard existing properties."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError(f"invalid or duplicate property: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


@dataclass(frozen=True)
class Note:
    metadata: dict
    body: str


def read_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return Note({}, text)
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in {"---", "..."}), None)
    if end is None:
        raise ValueError("frontmatter has no closing delimiter")
    metadata = yaml.load("".join(lines[1:end]), Loader=UniqueKeyLoader)
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return Note(metadata, "".join(lines[end + 1:]))


def within(path: Path, directory: Path) -> bool:
    return path.resolve().is_relative_to(directory.resolve())


def relative_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ConfigError("paths must be non-empty relative paths using forward slashes")
    path = Path(value)
    if path.is_absolute() or path.drive or value.startswith("/") or any(x in {"..", ".git", ".obsidian", ".cache"} for x in path.parts):
        raise ConfigError(f"unsafe path: {value!r}")
    resolved = (root / path).resolve()
    if resolved == root or not within(resolved, root):
        raise ConfigError(f"path escapes knowledge base: {value!r}")
    return resolved


@dataclass(frozen=True)
class KnowledgeBase:
    root: Path
    paths: dict[str, Path]

    @classmethod
    def load(cls, root: Path):
        root = root.resolve(strict=True)
        config_file = root / "kb.toml"
        if not within(config_file, root):
            raise ConfigError("kb.toml escapes knowledge base")
        config = tomllib.loads(config_file.read_text(encoding="utf-8-sig"))
        if config.get("version") != 1:
            raise ConfigError("kb.toml requires version = 1")
        values = config.get("paths", {})
        expected = set(DIRECTORIES + SPECIAL_FILES)
        if not isinstance(values, dict) or set(values) != expected:
            raise ConfigError(f"paths must contain exactly {', '.join(sorted(expected))}")
        paths = {name: relative_path(root, value) for name, value in values.items()}
        paths["notes"] = relative_path(root, "Notes")
        directories = [paths[name] for name in (*DIRECTORIES, "notes")]
        for i, directory in enumerate(directories):
            for other in directories[i + 1:]:
                if within(directory, other) or within(other, directory):
                    raise ConfigError("raw/wiki/Notes/reports/templates directories must not overlap")
        for name in SPECIAL_FILES:
            if paths[name] == paths["wiki"] or not within(paths[name], paths["wiki"]) or paths[name].suffix != ".md":
                raise ConfigError(f"{name} must be a Markdown file inside the wiki directory")
        if len({paths[name] for name in SPECIAL_FILES}) != len(SPECIAL_FILES):
            raise ConfigError("index, log and overview must be distinct files")
        return cls(root, paths)


def files_under(root: Path):
    """Do not follow junctions or symbolic links into another knowledge base."""
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        kept = []
        for name in sorted(names):
            child = base / name
            if name in SKIP_DIRECTORIES:
                continue
            if child.is_symlink() or child.is_junction():
                raise ConfigError(f"linked directory requires separate review: {child}")
            kept.append(name)
        names[:] = kept
        for name in sorted(files):
            path = base / name
            if path.is_symlink() or not within(path, root):
                raise ConfigError(f"linked file requires separate review: {path}")
            yield path
