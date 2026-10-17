from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CoupleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invite_code: str
    created_at: datetime