from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.couple import Couple
    from api.v1.models.user import User


class Event(BaseModel):
    __tablename__ = "events"

    couple_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    module: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    couple: Mapped[Couple] = relationship(back_populates="events")
    user: Mapped[User] = relationship(back_populates="events")