import json

from langchain_core.language_models.fake_chat_models import FakeListChatModel

import termdiff.llm as llm
from termdiff.cli import main

OLD = "1. Fees\n\nFees are $5 a month.\n\n2. Data\n\nWe never sell your data.\n"
NEW = "1. Fees\n\nFees are $7 a month.\n\n2. Data\n\nWe never sell your data.\n"


def write(tmp_path, old=OLD, new=NEW):
    a, b = tmp_path / "old.txt", tmp_path / "new.txt"
    a.write_text(old)
    b.write_text(new)
    return str(a), str(b)


def test_no_llm_lists_changes(tmp_path, capsys):
    assert main([*write(tmp_path), "--no-llm"]) == 0
    assert capsys.readouterr().out == "modified: Fees are [-$5-] {+$7+} a month.\n\n"


def test_identical_files(tmp_path, capsys):
    assert main([*write(tmp_path, OLD, OLD), "--no-llm"]) == 0
    assert capsys.readouterr().out == "No changes found.\n"


def test_review_as_json(tmp_path, capsys):
    answer = {
        "topic": "fees",
        "impact": "worse",
        "severity": 3,
        "summary": "Fee rises to $7.",
        "quote": "$7 a month",
    }
    model = FakeListChatModel(responses=[json.dumps(answer)])
    assert main([*write(tmp_path), "--json"], model=model) == 0
    (item,) = json.loads(capsys.readouterr().out)
    assert item["topic"] == "fees"
    assert item["quote_found"] is True


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "a.txt"), str(tmp_path / "b.txt"), "--no-llm"]) == 1
    assert capsys.readouterr().err.startswith("termdiff: ")


def test_min_severity_hides_small_changes(tmp_path, capsys, monkeypatch):
    old = "Fees are $5 a month.\n\nWe use cookies to remember you.\n"
    new = "Fees are $7 a month.\n\nWe use cookies to remember your settings.\n"
    fee = {"topic": "fees", "impact": "worse", "severity": 3, "summary": "Fee up", "quote": "$7"}
    cookie = fee | {"topic": "privacy", "severity": 1, "summary": "Cookie wording", "quote": "x"}
    model = FakeListChatModel(responses=[json.dumps(fee), json.dumps(cookie)])
    # One change at a time so the fake model's answers line up with the changes.
    original = llm.review
    monkeypatch.setattr(llm, "review", lambda c, m: original(c, m, max_concurrency=1))
    assert main([*write(tmp_path, old, new), "--min-severity", "2"], model=model) == 0
    out = capsys.readouterr().out
    assert "Fee up" in out
    assert "Cookie wording" not in out


def test_no_llm_with_json_prints_json(tmp_path, capsys):
    assert main([*write(tmp_path), "--no-llm", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        {"kind": "modified", "old": "Fees are $5 a month.", "new": "Fees are $7 a month."}
    ]


def test_missing_api_key_is_a_clear_error(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert main([*write(tmp_path)]) == 1
    assert "GROQ_API_KEY is not set" in capsys.readouterr().err
