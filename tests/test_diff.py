from termdiff.diff import paragraphs


def test_paragraphs_split_on_blank_lines_and_unwrap():
    text = "1. Fees\n\nWe may change\n   fees.\n \n\n2. Ending\n"
    assert paragraphs(text) == ["1. Fees", "We may change fees.", "2. Ending"]


def test_empty_text_has_no_paragraphs():
    assert paragraphs("\n\n  \n") == []
