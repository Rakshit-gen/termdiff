"""Score the model's reviews of the Shelfspace example against hand written labels.

    uv run python examples/run_eval.py

Needs GROQ_API_KEY. Each change is matched to a label by a phrase in its text.
A change passes when the topic is one of the accepted topics, the impact is one
of the accepted impacts, the severity is at least the label's minimum, and the
model's quote appears in the change.
"""

import json
import time
from pathlib import Path

from termdiff.diff import diff_paragraphs, paragraphs
from termdiff.llm import groq_model, review
from termdiff.load import load_text

HERE = Path(__file__).parent


def main() -> int:
    labels = json.loads((HERE / "shelfspace_labels.json").read_text())
    old = paragraphs(load_text(HERE / "shelfspace_2025.txt"))
    new = paragraphs(load_text(HERE / "shelfspace_2026.txt"))
    changes = diff_paragraphs(old, new)
    if len(changes) != len(labels):
        print(f"expected {len(labels)} changes from the diff, got {len(changes)}")
        return 1

    started = time.monotonic()
    reviewed = review(changes, groq_model())
    elapsed = time.monotonic() - started

    passed = 0
    for r in reviewed:
        text = r.change.old + " " + r.change.new
        label = next(lb for lb in labels if lb["match"] in text)
        a = r.assessment
        problems = []
        if a is None:
            problems.append("no assessment")
        else:
            if a.topic not in label["topics"]:
                problems.append(f"topic {a.topic}")
            if a.impact not in label["impact"]:
                problems.append(f"impact {a.impact}")
            if a.severity < label["min_severity"]:
                problems.append(f"severity {a.severity} < {label['min_severity']}")
            if not r.quote_found:
                problems.append(f"quote not found: {a.quote!r}")
        passed += not problems
        status = "PASS" if not problems else "FAIL  " + ", ".join(problems)
        print(f"{status:40}  {label['match']}")
    print(f"\n{passed}/{len(labels)} changes passed in {elapsed:.1f}s")
    return 0 if passed == len(labels) else 1


if __name__ == "__main__":
    raise SystemExit(main())
