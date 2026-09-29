"""Classify each change with a chat model through LangChain."""

from typing import Literal

from pydantic import BaseModel, Field

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
