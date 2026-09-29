from termdiff.diff import Change
from termdiff.llm import Assessment, Reviewed
from termdiff.report import render


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
    r = Reviewed(Change("removed", "You can sue us.", ""), None)
    out = render([r])
    assert "Not reviewed" in out
    assert "Removed: You can sue us." in out


def test_no_changes():
    assert render([]) == "No changes found.\n"
