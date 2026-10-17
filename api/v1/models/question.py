from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.daily_prompt import DailyPrompt


class Question(BaseModel):
    __tablename__ = "questions"

    category: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    daily_prompts: Mapped[list[DailyPrompt]] = relationship(back_populates="question")