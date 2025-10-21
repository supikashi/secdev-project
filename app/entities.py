from typing import Optional

from pydantic import BaseModel


class SuggestionCreate(BaseModel):
    title: str
    text: str
    status: Optional[str] = "new"


class SuggestionOut(BaseModel):
    id: int
    user_id: int
    title: str
    text: str
    status: Optional[str] = "new"
