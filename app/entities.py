from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SuggestionStatus(str, Enum):
    new = "new"
    reviewing = "reviewing"
    approved = "approved"
    rejected = "rejected"


class SuggestionCreate(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, description="Suggestion title"
    )
    text: str = Field(..., min_length=1, max_length=5000, description="Suggestion text")
    status: Optional[SuggestionStatus] = SuggestionStatus.new

    @field_validator("title", "text")
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        if v:
            v = "".join(char for char in v if ord(char) >= 32 or char in "\n\r\t")
        return v


class SuggestionOut(BaseModel):
    id: int
    user_id: int
    title: str
    text: str
    status: str
