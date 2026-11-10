import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .models import StaffUser


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def check_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hmac.compare_digest(candidate, digest)


def make_token(user: StaffUser) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"sub": user.id, "exp": expires}, config.JWT_SECRET, algorithm="HS256")


def current_staff(authorization: str = Header(""), db: Session = Depends(get_db)) -> StaffUser:
    try:
        payload = jwt.decode(authorization.removeprefix("Bearer "), config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Please sign in")
    user = db.get(StaffUser, payload["sub"])
    if not user:
        raise HTTPException(401, "Please sign in")
    return user


def current_admin(user: StaffUser = Depends(current_staff)) -> StaffUser:
    if not user.is_admin:
        raise HTTPException(403, "Only an administrator can change agent settings")
    return user


def agent_only(x_agent_key: str = Header("")) -> None:
    if not hmac.compare_digest(x_agent_key, config.AGENT_API_KEY):
        raise HTTPException(401, "Invalid agent key")
