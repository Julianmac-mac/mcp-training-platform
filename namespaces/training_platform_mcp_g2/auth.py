import logging
from typing import Any, Dict, Optional

import httpx
from ffmcp import GO_BASE_PATH

logger = logging.getLogger(__name__)
TOKEN_INFO_URL = f"{GO_BASE_PATH}/auth/token/info"


async def resolve_user_email(access_token: str) -> str:
    if not access_token:
        raise ValueError("Access token is required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(TOKEN_INFO_URL, params={"access_token": access_token})
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Token validation failed: %s", exc)
            raise ValueError("Invalid or expired token") from exc

        payload: Dict[str, Any] = response.json()

    user_email = payload.get("email") or payload.get("user_email") or payload.get("user")
    if not user_email:
        logger.error("Token info response missing email: %s", payload)
        raise ValueError("Token validation response did not include a user email")

    return str(user_email)


def extract_access_token(ctx: Any) -> Optional[str]:
    access_token = None
    try:
        access_token = ctx.get_state("access_token")
    except Exception:
        access_token = None

    if access_token:
        return access_token

    request = None
    try:
        request = ctx.get_state("request")
    except Exception:
        request = None

    if request is not None:
        headers = getattr(request, "headers", None)
        if headers is not None:
            auth_header = headers.get("Authorization") or headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                return auth_header.split(" ", 1)[1].strip()
    return None
