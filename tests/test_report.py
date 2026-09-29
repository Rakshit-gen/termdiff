import json

from termdiff.diff import Change
from termdiff.llm import Assessment, Reviewed
from termdiff.report import render, to_json


def reviewed(kind, old, new, **a):
    base = dict(topic="other", impact="neutral", severity=1, summary="s", quote="x")
    return Reviewed(Change(kind, old, new), Assessment(**(base | a)))


def test_sorted_by_severity_then_worse_first():
    minor = reviewed("added", "", "We added a glossary.", summary="Glossary", quote="glossary")
    better = reviewed(
        "added",
        "",
        "Refunds within 30 days.",
        impact="better",
        severity=3,
        summary="Refunds",
        quote="Refunds",
    )
    worse = reviewed(
        "modified",
        "Fees are $5.",
        "Fees are $7.",
        topic="fees",
        impact="worse",
        severity=3,
        summary="Fee up",
        quote="$7",
    )
    out = render([minor, better, worse])
    assert out.index("Fee up") < out.index("Refunds") < out.index("Glossary")
    assert "## [3] fees: Worse for you" in out
    assert "Edited: Fees are [-$5.-] {+$7.+}" in out


def test_unverified_quote_is_flagged():
    r = reviewed("added", "", "We may share data.", quote="sell your data")
    assert "quoted words were not found" in render([r])


def test_unreadable_output_is_listed_not_hidden():
    r = Reviewed(
        Change("removed", "You can sue us.", ""), None, "RateLimitError: 429 slow down\nbody"
    )
    out = render([r])
    assert "Not reviewed" in out
    assert "The model call failed: RateLimitError: 429 slow down\n" in out
    assert "Removed: You can sue us." in out


def test_no_changes():
    assert render([]) == "No changes found.\n"


def test_json_output_includes_assessment_and_quote_check():
    r = reviewed("added", "", "Disputes go to arbitration.", topic="disputes", quote="arbitration")
    (item,) = json.loads(to_json([r]))
    assert item["kind"] == "added"
    assert item["topic"] == "disputes"
    assert item["quote_found"] is True


def test_json_output_for_unreviewed_change_has_no_assessment():
    (item,) = json.loads(to_json([Reviewed(Change("removed", "x", ""), None, "boom")]))
    assert item == {"kind": "removed", "old": "x", "new": "", "error": "boom"}
