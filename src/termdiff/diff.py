"""Find changed paragraphs between two versions of a document."""

import re


def paragraphs(text: str) -> list[str]:
    """Split on blank lines and collapse whitespace inside each paragraph."""
    blocks = re.split(r"\n\s*\n", text)
    return [" ".join(b.split()) for b in blocks if b.strip()]
