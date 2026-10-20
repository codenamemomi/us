from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CoupleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invite_code: str
    created_at: datetime


class PartnerInfo(BaseModel):
    id: UUID
    name: str
    email: str


class CoupleProfileResponse(BaseModel):
    couple_id: UUID
    invite_code: str
    created_at: datetime
    me: PartnerInfo
    partner: PartnerInfo | None = None
    streak: int
    days_together: int