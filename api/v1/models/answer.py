from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.daily_prompt import DailyPrompt
    from api.v1.models.user import User


class Answer(BaseModel):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("prompt_id", "user_id", name="uq_answers_prompt_user"),
    )

    prompt_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("daily_prompts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    prompt: Mapped[DailyPrompt] = relationship(back_populates="answers")
    user: Mapped[User] = relationship(back_populates="answers")