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
    """Pair each old paragraph with its most similar new one, best matches first."""
    # ponytail: compares every pair, O(n*m). Fine for edited sections; a full rewrite of
    # a very long document would want a cheaper first pass (for example word overlap).
    scored = sorted(
        ((_similar(o, n), i, j) for i, o in enumerate(olds) for j, n in enumerate(news)),
        reverse=True,
    )
    match: dict[int, int] = {}
    used_new: set[int] = set()
    for score, i, j in scored:
        if score < PAIR_THRESHOLD:
            break
        if i not in match and j not in used_new:
            match[i] = j
            used_new.add(j)
    changes = []
    for i, o in enumerate(olds):
        if i in match:
            changes.append(Change("modified", o, news[match[i]]))
        else:
            changes.append(Change("removed", o, ""))
    changes += [Change("added", "", n) for j, n in enumerate(news) if j not in used_new]
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
