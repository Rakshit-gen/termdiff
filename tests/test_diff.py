from termdiff.diff import Change, diff_paragraphs, paragraphs, word_diff


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


def test_typographic_edits_are_not_changes():
    old = ['We "may" end your account - at any time.']
    new = ["We \u201cmay\u201d end your account \u2014 at any time."]
    assert diff_paragraphs(old, new) == []


def test_case_only_edits_are_not_changes():
    assert diff_paragraphs(["GOVERNING LAW"], ["Governing law"]) == []


def test_real_edit_next_to_a_cosmetic_one_is_kept():
    old = ["We “may” end your account with notice."]
    new = ['We "may" end your account without notice.']
    assert [c.kind for c in diff_paragraphs(old, new)] == ["modified"]


def test_word_diff_marks_replacements_and_insertions():
    old = "We may end your account with 30 days notice."
    new = "We may end your account at any time without notice."
    assert word_diff(old, new) == (
        "We may end your account [-with 30 days-] {+at any time without+} notice."
    )


def test_word_diff_of_identical_text_is_the_text():
    assert word_diff("same words", "same words") == "same words"


def test_renumbered_headings_are_not_changes():
    old = ["5. Your photos", "6. Privacy", "(a) Cookies"]
    new = ["6. Your photos", "7. Privacy", "(b) Cookies"]
    assert diff_paragraphs(old, new) == []


def test_changes_come_out_in_document_order():
    old = ["Fees are $4.", "Refunds within 7 days.", "Photos are yours."]
    new = [
        "Fees are $6.",
        "Refunds within 30 days.",
        "Plans renew automatically.",
        "Photos are ours.",
    ]
    changes = diff_paragraphs(old, new)
    assert [c.new for c in changes] == [
        "Fees are $6.",
        "Refunds within 30 days.",
        "Plans renew automatically.",
        "Photos are ours.",
    ]


def test_a_changed_number_at_the_start_of_a_paragraph_is_a_real_change():
    old = ["30 days notice is required before any price change."]
    new = ["7 days notice is required before any price change."]
    assert [c.kind for c in diff_paragraphs(old, new)] == ["modified"]
