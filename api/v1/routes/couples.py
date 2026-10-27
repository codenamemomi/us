from fastapi import APIRouter, HTTPException, status

from api.core.dependencies import CurrentUser, DatabaseSession
from api.core.realtime import hub
from api.v1.schema.couple import (
    CoupleProfileResponse,
    CoupleResponse,
    UpdateAnniversaryRequest,
)
from api.v1.services.couple import create_couple, get_couple_profile, update_anniversary_date
from api.v1.services.engagement import partner_id_for

router = APIRouter(prefix="/couples", tags=["couples"])


@router.post("", response_model=CoupleResponse, status_code=status.HTTP_201_CREATED)
def create(db: DatabaseSession) -> CoupleResponse:
    return create_couple(db)


@router.get("/me", response_model=CoupleProfileResponse)
def get_my_couple(db: DatabaseSession, user: CurrentUser) -> CoupleProfileResponse:
    try:
        return get_couple_profile(db, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.patch("/anniversary", response_model=CoupleProfileResponse)
@router.put("/anniversary", response_model=CoupleProfileResponse)
async def update_anniversary(
    body: UpdateAnniversaryRequest,
    db: DatabaseSession,
    user: CurrentUser,
) -> CoupleProfileResponse:
    try:
        profile = update_anniversary_date(db, user, body.anniversary_date)
        pid = partner_id_for(db, user.id)
        if pid:
            await hub.publish(
                pid,
                {
                    "type": "anniversary_updated",
                    "anniversary_date": str(body.anniversary_date) if body.anniversary_date else None,
                },
            )
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e