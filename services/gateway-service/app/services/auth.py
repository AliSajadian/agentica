'''Authentication'''
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import User, RefreshToken
from app.core.security import security_service
from app.models.schemas import (
    RegisterRequest, LoginRequest,
    TokenResponse, UserResponse, UserRole
)
from app.config import settings
from app.utils.logger import get_logger
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
import hashlib
import uuid

logger = get_logger(__name__)


class AuthService:
    """Handles user registration, login, token management."""

    async def register(
        self,
        db: AsyncSession,
        request: RegisterRequest
    ) -> UserResponse:
        """Register a new user — raises 409 if email already exists."""
        # check email uniqueness
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        user = User(
            email=request.email,
            hashed_password=security_service.hash_password(request.password),
            full_name=request.full_name,
            role=UserRole.user
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return UserResponse.model_validate(user)

    async def login(
        self,
        db: AsyncSession,
        request: LoginRequest
    ) -> TokenResponse:
        """Authenticate user and return JWT access + refresh tokens."""
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not security_service.verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        access_token = security_service.create_access_token(
            user_id=str(user.id),
            role=user.role
        )
        refresh_token = security_service.create_refresh_token(
            user_id=str(user.id),
            role=user.role
        )

        # store hashed refresh token
        await self._store_refresh_token(db, user.id, refresh_token)

        logger.info("user_logged_in", user_id=str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def refresh(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> TokenResponse:
        """Issue new access token using a valid refresh token."""
        # validate token
        payload = security_service.decode_token(refresh_token)
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # check token not revoked
        token_hash = self._hash_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False)  # noqa: E712
            )
        )
        stored_token = result.scalar_one_or_none()
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or not found"
            )

        # revoke old token and issue new tokens
        stored_token.is_revoked = True
        new_access = security_service.create_access_token(payload.sub, payload.role)
        new_refresh = security_service.create_refresh_token(payload.sub, payload.role)
        await self._store_refresh_token(db, uuid.UUID(payload.sub), new_refresh)

        logger.info("tokens_refreshed", user_id=payload.sub)
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> UserResponse | None:
        """Retrieve a user by their UUID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def _store_refresh_token(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        token: str
    ):
        """Store a hashed refresh token with expiry in the database."""
        token_record = RefreshToken(
            user_id=user_id,
            token_hash=self._hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        )
        db.add(token_record)
        await db.flush()

    def _hash_token(self, token: str) -> str:
        """Hash a token string for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()


auth_service = AuthService()
