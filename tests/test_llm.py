import json

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from termdiff.diff import Change
from termdiff.llm import review


def assessment(**overrides):
    base = {
        "topic": "fees",
        "impact": "worse",
        "severity": 3,
        "summary": "The monthly fee goes up from $5 to $7.",
        "quote": "$7 a month",
    }
    return json.dumps(base | overrides)


FEE_CHANGE = Change("modified", "Fees are $5 a month.", "Fees are $7 a month.")


def test_review_parses_the_model_answer():
    model = FakeListChatModel(responses=[assessment()])
    (r,) = review([FEE_CHANGE], model, max_concurrency=1)
    assert r.change is FEE_CHANGE
    assert r.assessment.topic == "fees"
    assert r.assessment.severity == 3


def test_review_keeps_order_across_changes():
    added = Change("added", "", "Disputes go to arbitration.")
    model = FakeListChatModel(
        responses=[assessment(), assessment(topic="disputes", quote="arbitration")]
    )
    results = review([FEE_CHANGE, added], model, max_concurrency=1)
    assert [r.assessment.topic for r in results] == ["fees", "disputes"]


def test_out_of_range_severity_is_retried_then_dropped():
    model = FakeListChatModel(responses=[assessment(severity=5), assessment(severity=9)])
    (r,) = review([FEE_CHANGE], model, max_concurrency=1)
    assert r.assessment is None
    assert r.change is FEE_CHANGE
    assert r.error.startswith("OutputParserException")


def test_quote_found_ignores_case_quotes_and_trailing_period():
    model = FakeListChatModel(responses=[assessment(quote="“FEES ARE $7 a month.”")])
    (r,) = review([FEE_CHANGE], model, max_concurrency=1)
    assert r.quote_found


def test_invented_quote_is_not_found():
    model = FakeListChatModel(responses=[assessment(quote="no refunds ever")])
    (r,) = review([FEE_CHANGE], model, max_concurrency=1)
    assert not r.quote_found


def test_empty_quote_is_not_found():
    model = FakeListChatModel(responses=[assessment(quote="  ")])
    (r,) = review([FEE_CHANGE], model, max_concurrency=1)
    assert not r.quote_found
