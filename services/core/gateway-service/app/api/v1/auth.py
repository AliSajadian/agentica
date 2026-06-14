'''Authentication'''
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.core.security import security_service, bearer_scheme
from app.services.auth import auth_service
from app.models.schemas import (
    RegisterRequest, LoginRequest,
    TokenResponse, RefreshRequest,
    UserResponse
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    try:
        logger.info("register_started", email=request.email)
        return await auth_service.register(db=db, request=request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("register_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    try:
        logger.info("login_started", email=request.email)
        return await auth_service.login(db=db, request=request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Issue new access token using a valid refresh token."""
    try:
        return await auth_service.refresh(
            db=db,
            refresh_token=request.refresh_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("refresh_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Return current authenticated user profile."""
    try:
        payload = await security_service.get_current_user(credentials)
        from uuid import UUID
        user = await auth_service.get_user_by_id(db=db, user_id=UUID(payload.sub))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_me_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
