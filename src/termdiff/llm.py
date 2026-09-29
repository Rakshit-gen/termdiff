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
