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
    # Compare normalized text so "GOVERNING LAW" and "Governing law" pair up and are
    # then dropped as cosmetic, instead of showing as a removal plus an addition.
    return SequenceMatcher(None, normalize(a), normalize(b), autojunk=False).ratio()


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
    # Keep document order: sort by position in the new version, placing a removed
    # paragraph where it used to sit.
    placed = []
    for i, o in enumerate(olds):
        if i in match:
            placed.append((match[i], Change("modified", o, news[match[i]])))
        else:
            placed.append((i - 0.5, Change("removed", o, "")))
    placed += [(j, Change("added", "", n)) for j, n in enumerate(news) if j not in used_new]
    return [c for _, c in sorted(placed, key=lambda p: p[0])]


# Typographic swaps that editors and CMSes make without changing meaning.
COSMETIC = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}
)


# "12.", "4.2", "(b)" and similar at the start of a paragraph. Inserting a section
# renumbers every heading after it, which is not a change in meaning.
#
# A bare number is not a clause number: "30 days notice" must not become "days
# notice", or a change from 30 to 7 days would be dropped as cosmetic. So the
# number needs a trailing dot ("12.") or an inner one ("4.2").
CLAUSE_NUMBER_RE = re.compile(r"^\s*(?:\d+\.(?:\d+\.?)*|\(?[a-z]\))\s+")


def normalize(p: str) -> str:
    p = CLAUSE_NUMBER_RE.sub("", p.translate(COSMETIC).lower())
    return " ".join(p.split())


def is_cosmetic(change: Change) -> bool:
    return change.kind == "modified" and normalize(change.old) == normalize(change.new)


def diff_paragraphs(old: list[str], new: list[str]) -> list[Change]:
    """Changed paragraphs, oldest position first. Quote, dash and case edits are dropped."""
    changes = []
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "delete":
            changes += [Change("removed", p, "") for p in old[i1:i2]]
        elif op == "insert":
            changes += [Change("added", "", p) for p in new[j1:j2]]
        elif op == "replace":
            changes += _pair_up(old[i1:i2], new[j1:j2])
    return [c for c in changes if not is_cosmetic(c)]


def word_diff(old: str, new: str) -> str:
    """Show an edit inline, git style: [-removed words-] {+added words+}."""
    a, b = old.split(), new.split()
    out = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(" ".join(a[i1:i2]))
            continue
        if i2 > i1:
            out.append("[-" + " ".join(a[i1:i2]) + "-]")
        if j2 > j1:
            out.append("{+" + " ".join(b[j1:j2]) + "+}")
    return " ".join(out)
