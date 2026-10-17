from fastapi import APIRouter, status

from api.core.dependencies import DatabaseSession
from api.v1.schema.couple import CoupleResponse
from api.v1.services.couple import create_couple

router = APIRouter(prefix="/couples", tags=["couples"])


@router.post("", response_model=CoupleResponse, status_code=status.HTTP_201_CREATED)
def create(db: DatabaseSession) -> CoupleResponse:
    return create_couple(db)