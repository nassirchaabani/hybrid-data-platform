import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.config import Settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(subject: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def constant_time_equal(value: str, expected: str) -> bool:
    """Compare deux valeurs sans arrêt anticipé."""
    return hmac.compare_digest(
        hashlib.sha256(value.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )


def current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> str:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton absent ou invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings: Settings = request.app.state.settings
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise unauthorized from exc
    subject = payload.get("sub")
    if not subject:
        raise unauthorized
    return str(subject)
