from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: UUID
    category: str
    text: str


class DailyPromptResponse(BaseModel):
    prompt_id: UUID
    date: date
    question: QuestionOut
    my_answer: str | None = None
    partner_answered: bool = False
    both_answered: bool = False
    partner_answer: str | None = None


class AnswerPromptRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
