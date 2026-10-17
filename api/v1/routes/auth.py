from fastapi import APIRouter, HTTPException, status

from api.core.dependencies import DatabaseSession
from api.core.security import create_access_token
from api.v1.schema.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from api.v1.services.auth import authenticate_user, register_user
from api.v1.services.errors import ServiceError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: DatabaseSession) -> RegisterResponse:
    try:
        user, couple = register_user(db, request)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return RegisterResponse(user=user, couple_id=couple.id)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: DatabaseSession) -> TokenResponse:
    try:
        user = authenticate_user(db, request)
    except ServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return TokenResponse(access_token=create_access_token(user.id))