from termdiff.diff import Change, diff_paragraphs, paragraphs


def test_paragraphs_split_on_blank_lines_and_unwrap():
    text = "1. Fees\n\nWe may change\n   fees.\n \n\n2. Ending\n"
    assert paragraphs(text) == ["1. Fees", "We may change fees.", "2. Ending"]


def test_empty_text_has_no_paragraphs():
    assert paragraphs("\n\n  \n") == []


def test_unchanged_documents_have_no_changes():
    doc = ["A", "B"]
    assert diff_paragraphs(doc, doc) == []


def test_added_removed_and_modified():
    old = ["Intro.", "We never sell your data.", "Fees are $5 a month.", "Contact us."]
    new = ["Intro.", "Fees are $7 a month.", "Disputes go to arbitration.", "Contact us."]
    changes = diff_paragraphs(old, new)
    assert Change("removed", "We never sell your data.", "") in changes
    assert Change("modified", "Fees are $5 a month.", "Fees are $7 a month.") in changes
    assert Change("added", "", "Disputes go to arbitration.") in changes
    assert len(changes) == 3


def test_unrelated_replacement_is_not_paired():
    changes = diff_paragraphs(["Cookies help us."], ["You waive class actions entirely."])
    assert [c.kind for c in changes] == ["removed", "added"]
