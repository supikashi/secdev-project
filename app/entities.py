from typing import Optional

from pydantic import BaseModel


class SuggestionIn(BaseModel):
    user_id: int
    title: str
    text: str
    status: Optional[str] = "new"


class SuggestionOut(SuggestionIn):
    id: int
