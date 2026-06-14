'''Security'''
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.models.schemas import TokenPayload, UserRole
from app.utils.logger import get_logger
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi import Request

logger = get_logger(__name__)

# password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP bearer scheme for JWT extraction
bearer_scheme = HTTPBearer()


class SecurityService:
    """Handles JWT creation, validation and password hashing."""

    def hash_password(self, password: str) -> str:
        """Hash a plain text password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a plain text password against a hashed password."""
        return pwd_context.verify(plain, hashed)

    def create_access_token(self, user_id: str, role: UserRole) -> str:
        """Create a signed JWT access token with expiry."""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, user_id: str, role: UserRole) -> str:
        """Create a signed JWT refresh token with longer expiry."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    def decode_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT token, raising 401 if invalid."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenPayload(**payload)
        except JWTError as e:
            logger.warning("token_decode_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            ) from e

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials
    ) -> TokenPayload:
        """Extract and validate current user from bearer token."""
        token = credentials.credentials
        payload = self.decode_token(token)
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload

    def require_role(self, required_role: UserRole):
        """Dependency factory — raises 403 if user lacks required role."""
        async def check_role(payload: TokenPayload) -> TokenPayload:
            """Verify user has the required role."""
            role_hierarchy = {
                UserRole.readonly: 0,
                UserRole.user: 1,
                UserRole.admin: 2
            }
            if role_hierarchy[payload.role] < role_hierarchy[required_role]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return payload
        return check_role


security_service = SecurityService()
