"""Load a document as plain text."""

import re
from html.parser import HTMLParser
from pathlib import Path

# Tags that end a paragraph. Their closing tag becomes a blank line.
# br is not here: it is a line break inside a paragraph, handled in handle_starttag.
# Listing it made "<br/>" end a paragraph while "<br>" did not.
BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "section", "tr"}
CELL_TAGS = {"td", "th"}
# head holds the page title and metadata, which are not part of the terms and
# were being glued onto the first paragraph.
SKIP_TAGS = {"head", "script", "style", "nav", "header", "footer", "noscript"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n\n")
        elif tag in CELL_TAGS:
            # Keep cells in a row apart: "<td>Plus</td><td>$4</td>" was "Plus$4".
            self.parts.append(" | ")

    def handle_data(self, data):
        if not self.skip_depth:
            # Collapse runs of whitespace but keep one space, so "<b>30 days</b> notice"
            # does not turn into "30 daysnotice".
            self.parts.append(re.sub(r"\s+", " ", data))


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = [line.strip() for line in "".join(parser.parts).split("\n")]
    return "\n".join(lines)


def load_text(path: str | Path) -> str:
    path = Path(path)
    # utf-8-sig drops a byte order mark. Without it, the same text saved by an editor
    # that adds one showed up as a change to the first paragraph.
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    if path.suffix.lower() in {".html", ".htm"}:
        return html_to_text(raw)
    return raw
