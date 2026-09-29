# termdiff

See what changed between two versions of a terms of service, and which changes
matter.

termdiff lines up the two documents paragraph by paragraph, drops edits that do
not change meaning, and asks a chat model (through LangChain) to say what each
remaining change means for the user: the topic, whether it is worse or better,
and how serious it is. Every answer must quote the changed text, and answers
whose quote is not really there are flagged.

## Quickstart

```
uv sync
export GROQ_API_KEY=...
uv run termdiff examples/shelfspace_2025.txt examples/shelfspace_2026.txt --min-severity 3
```

Real output from that command, first two of four entries:

````
# 4 changes

## [3] fees: Worse for you

You now get less free storage, pay more for the Plus plan, and get shorter notice of price changes.

```
Edited: The Basic plan is free up to [-5-] {+2+} GB. The Plus plan costs [-$4-] {+$6+} a month for 200 GB. We will give you [-30-] {+7+} days notice by email before any price change.
```

## [3] termination: Worse for you

The company can now suspend or close your account without any notice, removing the previous 14-day warning.

```
Edited: You can close your account at any time. We may {+suspend or+} close your account [-if you break these terms,-] {+at any time+} and [-we will tell you 14 days before we do, unless the law requires faster action.-] {+without notice.+}
```
````

| Flag | What it does |
|---|---|
| `--no-llm` | List the changes only. Needs no API key. |
| `--json` | Print JSON instead of Markdown. |
| `--min-severity N` | Hide reviewed changes below severity N (1 to 3). Failed reviews are always shown. |

Inputs can be `.txt`, `.md` or `.html`. HTML is stripped to paragraphs with the
standard library parser, dropping scripts, styles, nav, header and footer.

The model defaults to `openai/gpt-oss-120b` on Groq. Set `TERMDIFF_MODEL` to
use another one. Shelfspace is a made up company and both example documents
were written for this repo.

## How it works

1. Both documents are split into paragraphs on blank lines.
2. `difflib.SequenceMatcher` aligns the two paragraph lists. Inside a rewritten
   stretch, each old paragraph is paired with its most similar new one, so an
   edit shows as one edit rather than a removal plus an addition.
3. Edits that only change curly quotes, dashes, case or clause numbers are
   dropped. Adding a section renumbers every heading after it, and none of
   that is reported.
4. Each remaining change goes through `prompt | ChatGroq | PydanticOutputParser`.
   Changes are reviewed in parallel with LangChain's `batch`. Output that does
   not fit the schema is retried once.
5. A change whose review still fails stays in the report as "Not reviewed",
   with the error, instead of disappearing.
6. The model's quote is checked against the change text after the same
   normalization. If it is not there, the report says so.

Tests use LangChain's `FakeListChatModel`, so `uv run pytest` needs no key and
no network.

## Measured vs Claimed

| Claim | Value | How measured | Date |
|---|---|---|---|
| Example changes reviewed as labeled | 9 of 10, on 3 of 3 runs | `uv run python examples/run_eval.py`, `openai/gpt-oss-120b` on Groq, labels in `examples/shelfspace_labels.json` | 2026-09-29 |
| The one miss | same change each run | Sharing data with advertising partners was rated severity 2. The label, and the prompt, say 3 | 2026-09-29 |
| Model quotes found in the change text | 10 of 10, on 3 of 3 runs | Same runs | 2026-09-29 |
| Wall time for the 10 reviews | 2.1 to 3.4 s | Same runs, 4 calls in parallel | 2026-09-29 |

The eval is one pair of short documents with 10 changes, labeled by the person
who wrote them. It shows the pipeline works end to end. It is not evidence of
accuracy on real, long legal documents.

## Status

Known limits:

- Paragraphs are split on blank lines, or on single line breaks when the
  document has no blank lines at all. A document that mixes both, with single
  breaks between some clauses, will still join those clauses.
- A paragraph that starts with a decimal, like "3.5 GB of storage", looks the
  same as clause 3.5. If only that number changes, the edit is dropped as
  renumbering.
- Pairing inside a rewritten stretch compares every old paragraph with every
  new one. A full rewrite of a very long document will be slow.
- One eval run had every review fail. The cause was not recorded because
  errors were being dropped at the time; they are now kept and shown. The next
  runs passed, so a rate limit is the likely cause, but that is a guess.
- The model sees one change at a time, so it can miss changes that only matter
  together.
- This is not legal advice.
