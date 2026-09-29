"""Load a document as plain text."""

from pathlib import Path


def load_text(path: str | Path) -> str:
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    return raw.replace("\r\n", "\n").replace("\r", "\n")
