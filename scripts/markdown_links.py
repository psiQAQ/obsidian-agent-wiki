"""Bounded Markdown parsing shared by navigation and literal evidence checks.

Supports inline links, single-line reference definitions, full/collapsed
references and images. Not a complete CommonMark or Obsidian parser.
"""

from dataclasses import dataclass
import re


FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
WIKI_LINK = re.compile(r"!?\[\[([^\]\n]+)\]\]")
DESTINATION = r'(<[^<>\n]*>|[^\s<>]+?)'
TITLE = r'''(?:[ \t]+(?:"[^"\n]*"|'[^'\n]*'|\([^()\n]*\)))?'''
DEFINITION = re.compile(r'^ {0,3}\[([^\[\]\n]+)\]:[ \t]*' + DESTINATION + TITLE + r'[ \t]*$', re.M)
LINK = re.compile(
    r'!?\[([^\[\]\n]*)\](?:\(\s*(<[^<>\n]*>|[^\s()]+)' + TITLE
    + r'\s*\)|\[([^\[\]\n]*)\])'
)


def prose(text: str) -> str:
    """Remove code blocks and HTML comments, preserving line positions."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            lines.append("")
        elif marker and not (marker[1][0] == "`" and "`" in marker[2]):
            fence = marker[1]
            lines.append("")
        else:
            lines.append(line)
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m[0].count("\n"), "\n".join(lines), flags=re.S)


def label_key(value: str) -> str:
    return " ".join(value.split()).casefold()


@dataclass(frozen=True)
class MarkdownLink:
    target: str
    label: str
    line: int
    start: int
    end: int


@dataclass(frozen=True)
class Markdown:
    text: str
    links: tuple[MarkdownLink, ...]

    def visible(self) -> str:
        text = self.text
        for link in reversed(self.links):
            text = text[:link.start] + link.label + text[link.end:]
        return WIKI_LINK.sub(lambda m: m[1].split("|")[-1], text)


def parse_markdown(body: str) -> Markdown:
    text = re.sub(r"(`+)(.+?)\1", lambda m: "\n" * m[0].count("\n"), prose(body))
    definitions = {}
    for match in DEFINITION.finditer(text):
        # CommonMark: whitespace/case-insensitive labels; first definition wins.
        definitions.setdefault(label_key(match[1]), match[2].strip("<>"))
    text = DEFINITION.sub("", text)
    links = []
    for match in LINK.finditer(text):
        target = match[2]
        if target is None:
            target = definitions.get(label_key(match[3] or match[1]))
        if target is not None:
            links.append(MarkdownLink(target.strip("<>"), match[1], text.count("\n", 0, match.start()) + 1, match.start(), match.end()))
    return Markdown(text, tuple(links))
