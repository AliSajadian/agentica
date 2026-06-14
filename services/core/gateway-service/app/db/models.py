'''Models'''
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UuidPk
from app.models.schemas import UserRole
import uuid


class User(Base):
    """Represents a registered user in the gateway."""

    __tablename__ = "users"

    id: Mapped[UuidPk]
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class RefreshToken(Base):
    """Stores refresh tokens for token rotation and revocation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[UuidPk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
