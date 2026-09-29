"""Classify each change with a chat model through LangChain."""

import os
from dataclasses import dataclass
from typing import Literal

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from termdiff.diff import Change, normalize

Topic = Literal[
    "fees",
    "data_sharing",
    "privacy",
    "disputes",
    "termination",
    "liability",
    "content_license",
    "auto_renewal",
    "other",
]
Impact = Literal["worse", "better", "neutral"]


class Assessment(BaseModel):
    topic: Topic
    impact: Impact = Field(description="For the user, compared with the old version")
    severity: int = Field(ge=1, le=3, description="1 minor, 2 notable, 3 serious")
    summary: str = Field(description="One plain sentence a user would understand")
    quote: str = Field(description="Exact words copied from the changed text that show this")


SYSTEM_PROMPT = """You review one change between two versions of a terms of service.
Say what it means for an ordinary user.

- impact: worse if the user loses a right, pays more, shares more data or has less
  notice; better if the reverse; neutral if it only reorganizes or clarifies.
- severity: 3 for money, data sharing, giving up the right to sue, or ending the
  account without notice. 2 for things a careful user would want to know. 1 for
  small wording changes with little effect.
- quote: copy a short phrase exactly as written from the NEW text, or from the OLD
  text if the paragraph was removed. Do not paraphrase it.
- Only describe what the text says. Do not guess at the company's intent.

{format_instructions}"""

HUMAN_PROMPT = """Change type: {kind}

OLD:
{old}

NEW:
{new}"""


def build_chain(model: BaseChatModel) -> Runnable:
    parser = PydanticOutputParser(pydantic_object=Assessment)
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
    ).partial(format_instructions=parser.get_format_instructions())
    return (prompt | model | parser).with_retry(
        retry_if_exception_type=(OutputParserException,), stop_after_attempt=2
    )


@dataclass
class Reviewed:
    change: Change
    assessment: Assessment | None  # None when the call failed or the output was unreadable
    error: str | None = None

    @property
    def quote_found(self) -> bool:
        """True when the model's quote really appears in the changed text.

        A quote that is not there means the summary may describe something the
        document does not say, so the report flags it.
        """
        if self.assessment is None:
            return False
        quote = normalize(self.assessment.quote).strip(" .\"'")
        text = normalize(self.change.old + " " + self.change.new)
        return bool(quote) and quote in text


def review(changes: list[Change], model: BaseChatModel, max_concurrency: int = 4) -> list[Reviewed]:
    """One model call per change, run in parallel. Failures are kept with no assessment."""
    inputs = [{"kind": c.kind, "old": c.old or "(none)", "new": c.new or "(none)"} for c in changes]
    results = build_chain(model).batch(
        inputs, config={"max_concurrency": max_concurrency}, return_exceptions=True
    )
    return [
        Reviewed(c, r)
        if isinstance(r, Assessment)
        else Reviewed(c, None, f"{type(r).__name__}: {r}")
        for c, r in zip(changes, results, strict=True)
    ]


# Checked against Groq's model list on 2026-09-29. Override with TERMDIFF_MODEL.
DEFAULT_MODEL = "openai/gpt-oss-120b"


def groq_model() -> BaseChatModel:
    from langchain_groq import ChatGroq

    # gpt-oss reasons before answering and that counts against max_tokens, so keep
    # reasoning short and leave room for the JSON.
    return ChatGroq(
        model=os.environ.get("TERMDIFF_MODEL", DEFAULT_MODEL),
        temperature=0,
        reasoning_effort="low",
        max_tokens=4096,
    )
