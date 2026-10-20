from fastapi import APIRouter, HTTPException, status

from api.core.dependencies import CurrentUser, DatabaseSession
from api.v1.schema.couple import CoupleProfileResponse, CoupleResponse
from api.v1.services.couple import create_couple, get_couple_profile

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