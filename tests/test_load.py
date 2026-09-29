from termdiff.load import html_to_text, load_text


def test_text_files_get_unix_line_endings(tmp_path):
    p = tmp_path / "terms.txt"
    p.write_bytes(b"One\r\nTwo\rThree")
    assert load_text(p) == "One\nTwo\nThree"


def test_html_paragraphs_become_blocks_and_scripts_are_dropped():
    html = """
    <html><head><style>p { color: red }</style></head><body>
    <nav>Home | Pricing</nav>
    <h2>1. Fees</h2>
    <p>We may   change
       fees with <b>30 days</b> notice.</p>
    <script>track()</script>
    <ul><li>Refunds within 14 days.</li></ul>
    </body></html>
    """
    text = html_to_text(html)
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    assert blocks == [
        "1. Fees",
        "We may change fees with 30 days notice.",
        "Refunds within 14 days.",
    ]


def test_html_files_are_detected_by_extension(tmp_path):
    p = tmp_path / "terms.html"
    p.write_text("<p>Hello</p>")
    assert load_text(p).strip() == "Hello"


def test_byte_order_mark_is_dropped(tmp_path):
    p = tmp_path / "terms.txt"
    p.write_bytes(b"\xef\xbb\xbfFees are $5.")
    assert load_text(p) == "Fees are $5."
