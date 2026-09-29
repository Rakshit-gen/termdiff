"""Command line entry point."""

import argparse
import sys

from termdiff.diff import diff_paragraphs, paragraphs, word_diff
from termdiff.load import load_text


def main(argv: list[str] | None = None, model=None) -> int:
    parser = argparse.ArgumentParser(
        prog="termdiff",
        description="See what changed between two versions of a terms of service.",
    )
    parser.add_argument("old", help="old version (.txt, .md or .html)")
    parser.add_argument("new", help="new version (.txt, .md or .html)")
    parser.add_argument("--no-llm", action="store_true", help="list changes without review")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args(argv)

    try:
        old, new = load_text(args.old), load_text(args.new)
    except OSError as e:
        print(f"termdiff: {e}", file=sys.stderr)
        return 1

    changes = diff_paragraphs(paragraphs(old), paragraphs(new))

    if args.no_llm:
        for c in changes:
            text = word_diff(c.old, c.new) if c.kind == "modified" else (c.new or c.old)
            print(f"{c.kind}: {text}\n")
        if not changes:
            print("No changes found.")
        return 0

    from termdiff.llm import review
    from termdiff.report import render, to_json

    if model is None:
        from termdiff.llm import groq_model

        model = groq_model()

    reviewed = review(changes, model)
    sys.stdout.write(to_json(reviewed) if args.json else render(reviewed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
