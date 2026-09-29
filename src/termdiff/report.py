"""Write the review as Markdown or JSON."""

import json

from termdiff.diff import word_diff
from termdiff.llm import Reviewed

IMPACT_LABEL = {"worse": "Worse for you", "better": "Better for you", "neutral": "Neutral"}


def _sort_key(r: Reviewed):
    a = r.assessment
    if a is None:
        return (0, 0)
    # Most severe first, and within a severity, changes that hurt the user first.
    return (-a.severity, {"worse": 0, "neutral": 1, "better": 2}[a.impact])


def _change_text(r: Reviewed) -> str:
    c = r.change
    if c.kind == "added":
        return f"Added: {c.new}"
    if c.kind == "removed":
        return f"Removed: {c.old}"
    return f"Edited: {word_diff(c.old, c.new)}"


def render(reviewed: list[Reviewed]) -> str:
    if not reviewed:
        return "No changes found.\n"
    lines = [f"# {len(reviewed)} changes", ""]
    for r in sorted(reviewed, key=_sort_key):
        a = r.assessment
        if a is None:
            lines.append("## Not reviewed (the model output could not be read)")
        else:
            lines.append(f"## [{a.severity}] {a.topic}: {IMPACT_LABEL[a.impact]}")
            lines.append("")
            lines.append(a.summary)
            if not r.quote_found:
                lines.append("")
                lines.append("> Check this one: the quoted words were not found in the change.")
        lines += ["", "```", _change_text(r), "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def to_json(reviewed: list[Reviewed]) -> str:
    """Machine readable output, in the same order as the Markdown report."""
    items = []
    for r in sorted(reviewed, key=_sort_key):
        item = {"kind": r.change.kind, "old": r.change.old, "new": r.change.new}
        if r.assessment is not None:
            item |= r.assessment.model_dump()
            item["quote_found"] = r.quote_found
        items.append(item)
    return json.dumps(items, indent=2, ensure_ascii=False) + "\n"
