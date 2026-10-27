from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CoupleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invite_code: str
    created_at: datetime
    anniversary_date: date | None = None


class PartnerInfo(BaseModel):
    id: UUID
    name: str
    email: str


class UpdateAnniversaryRequest(BaseModel):
    anniversary_date: date | None = None


class CoupleProfileResponse(BaseModel):
    couple_id: UUID
    invite_code: str
    created_at: datetime
    anniversary_date: date | None = None
    me: PartnerInfo
    partner: PartnerInfo | None = None
    streak: int
    days_together: int