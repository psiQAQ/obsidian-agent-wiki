"""Literal candidates, adapted from Astro-Han/karpathy-llm-wiki (MIT).

See ../THIRD_PARTY_NOTICES.md. This is a bounded heuristic, not a fact checker.
Plain small integers, qualitative facts and paraphrases require semantic review.
"""

from dataclasses import dataclass
import re


NUMBER = re.compile(r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)*(?:\s*[KMB%](?![A-Za-z]))?|\d+(?:\.\d+)*(?:\s*[KMB%](?![A-Za-z]))?)(?![A-Za-z])")
DATE = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
QUOTES = [re.compile(r'"([^"\n]*)"'), re.compile(r"“([^”\n]*)”")]
LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
WIKILINK = re.compile(r"!?\[\[([^\]]*)\]\]")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True)
class Candidate:
    kind: str
    value: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def prose(text: str) -> str:
    lines = []
    fence = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker and not (marker[1][0] == "`" and "`" in marker[2]):
            fence = marker[1]
            continue
        lines.append(line)
    return re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)


def visible(text: str) -> str:
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = LINK.sub(r"\1", text)
    return WIKILINK.sub(lambda m: m[1].split("|")[-1], text)


def candidates(body: str) -> list[Candidate]:
    text = visible(prose(body))
    result = []
    for line in text.splitlines():
        spans = list(DATE.finditer(line))
        result.extend(Candidate("date", match[0]) for match in spans)
        remaining = list(line)
        for match in spans:
            remaining[match.start():match.end()] = " " * (match.end() - match.start())
        for match in NUMBER.finditer("".join(remaining)):
            value = match[0].strip()
            if re.search(r"[KMB%]$", value) or "," in value or "." in value or len(value) >= 4:
                result.append(Candidate("number", value))
    for paragraph in re.split(r"\n\s*\n", text):
        value = normalize(paragraph)
        for expression in QUOTES:
            result.extend(Candidate("quote", match[1]) for match in expression.finditer(value) if len(match[1].strip()) >= 15)
    block = []
    for line in text.splitlines() + [""]:
        if line.lstrip().startswith(">"):
            block.append(line.lstrip().lstrip(">").strip())
        else:
            value = normalize(" ".join(block))
            if len(value) >= 15:
                result.append(Candidate("quote", value))
            block.clear()
    return list(dict.fromkeys(result))


def contains(text: str, candidate: Candidate) -> bool:
    text = normalize(text)
    value = normalize(candidate.value)
    if candidate.kind == "quote":
        return value in text
    right = r"(?!-\d{2})" if candidate.kind == "date" and len(value) == 7 else ""
    return re.search(r"(?<![\d.,])" + re.escape(value) + right + r"(?![A-Za-z0-9]|[.,]\d|%)", text) is not None


def source_body(body: str) -> str:
    # Older Skill raw files have bookkeeping directly after their H1.
    # Only remove a leading metadata block, never an identical line in prose.
    lines = body.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if start is not None:
        i = start + 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        while i < len(lines) and re.match(r"^>\s*(Source|Collected|Published):", lines[i]):
            lines[i] = ""
            i += 1
    return "\n".join(lines)
