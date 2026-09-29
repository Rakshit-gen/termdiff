"""Find changed paragraphs between two versions of a document."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


def paragraphs(text: str) -> list[str]:
    """Split on blank lines and collapse whitespace inside each paragraph."""
    blocks = re.split(r"\n\s*\n", text)
    return [" ".join(b.split()) for b in blocks if b.strip()]


@dataclass(frozen=True)
class Change:
    kind: str  # "added", "removed" or "modified"
    old: str
    new: str


# Two paragraphs this similar are treated as one edited paragraph rather than a
# removal plus an addition. Picked by hand on the example documents.
PAIR_THRESHOLD = 0.5


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _pair_up(olds: list[str], news: list[str]) -> list[Change]:
    changes = []
    for i in range(max(len(olds), len(news))):
        o = olds[i] if i < len(olds) else None
        n = news[i] if i < len(news) else None
        if o is not None and n is not None and _similar(o, n) >= PAIR_THRESHOLD:
            changes.append(Change("modified", o, n))
            continue
        if o is not None:
            changes.append(Change("removed", o, ""))
        if n is not None:
            changes.append(Change("added", "", n))
    return changes


def diff_paragraphs(old: list[str], new: list[str]) -> list[Change]:
    changes = []
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "delete":
            changes += [Change("removed", p, "") for p in old[i1:i2]]
        elif op == "insert":
            changes += [Change("added", "", p) for p in new[j1:j2]]
        elif op == "replace":
            changes += _pair_up(old[i1:i2], new[j1:j2])
    return changes
