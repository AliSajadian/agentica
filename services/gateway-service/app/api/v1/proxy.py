'''Proxy'''
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import security_service, bearer_scheme
from app.core.rate_limiter import rate_limiter
from app.services.proxy import proxy_service
from app.models.schemas import TokenPayload
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenPayload:
    """Dependency — extracts and validates JWT from request."""
    return await security_service.get_current_user(credentials)


@router.post("/rag/{path:path}")
async def proxy_rag(
    path: str,
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Proxy authenticated requests to rag-service.
    Applies rate limiting per user before forwarding.
    """
    await rate_limiter.check(current_user.sub, f"rag/{path}")
    logger.info("proxy_rag", path=path, user=current_user.sub)
    return await proxy_service.forward(
        service="rag",
        path=f"/api/v1/{path}",
        method="POST",
        payload=payload,
        user_id=current_user.sub
    )


@router.post("/llm/{path:path}")
async def proxy_llm(
    path: str,
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Proxy authenticated requests to llm-service.
    Applies rate limiting per user before forwarding.
    """
    await rate_limiter.check(current_user.sub, f"llm/{path}")
    logger.info("proxy_llm", path=path, user=current_user.sub)
    return await proxy_service.forward(
        service="llm",
        path=f"/api/v1/{path}",
        method="POST",
        payload=payload,
        user_id=current_user.sub
    )


@router.post("/memory/{path:path}")
async def proxy_memory(
    path: str,
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Proxy authenticated requests to memory-service.
    Applies rate limiting per user before forwarding.
    """
    await rate_limiter.check(current_user.sub, f"memory/{path}")
    logger.info("proxy_memory", path=path, user=current_user.sub)
    return await proxy_service.forward(
        service="memory",
        path=f"/api/v1/{path}",
        method="POST",
        payload=payload,
        user_id=current_user.sub
    )


@router.post("/agent/{path:path}")
async def proxy_agent(
    path: str,
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Proxy authenticated requests to agent-service.
    Applies rate limiting per user before forwarding.
    """
    await rate_limiter.check(current_user.sub, f"agent/{path}")
    logger.info("proxy_agent", path=path, user=current_user.sub)
    return await proxy_service.forward(
        service="agent",
        path=f"/api/v1/{path}",
        method="POST",
        payload=payload,
        user_id=current_user.sub
    )


@router.get("/health/upstream")
async def upstream_health(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Return health status of all upstream services."""
    logger.info("current_user: ", current_user)
    return await proxy_service.health_check_all()
