import hmac
import logging
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from secrets import token_bytes
from uuid import uuid4

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.database_service import DatabaseService


router = APIRouter()
logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=False)
_local_users_by_email: dict[str, dict] = {}
_local_users_by_id: dict[str, dict] = {}

USER_ROLES = frozenset({"student", "staff", "admin"})


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    password_salt = salt or token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode(), password_salt, 120_000)
    return f"{password_salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", maxsplit=1)
        expected = _hash_password(password, bytes.fromhex(salt_hex)).split("$", maxsplit=1)[1]
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, digest_hex)


def _database_service(request: Request) -> DatabaseService:
    return request.app.state.database_service


def _create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication token signing is not configured",
        )
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": subject,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_access_token_minutes),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )


def _user_id(user: dict) -> str:
    if user.get("_id") is not None:
        return str(user["_id"])
    return str(user["id"])


def _public_user(user: dict) -> dict:
    result = {
        "id": _user_id(user),
        "email": user["email"],
        "role": user.get("role", "student"),
    }
    if user.get("department_id") is not None:
        result["department_id"] = str(user["department_id"])
    return result


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(credentials: Credentials, request: Request) -> dict[str, str]:
    email = _normalise_email(credentials.email)
    users = _database_service(request).users

    if users is not None:
        if await users.find_one({"email": email}):
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        await users.insert_one(
            {
                "email": email,
                "password_hash": _hash_password(credentials.password),
                "role": "student",
                "active": True,
                "created_at": datetime.now(timezone.utc),
            }
        )
    else:
        if email in _local_users_by_email:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = {
            "id": str(uuid4()),
            "email": email,
            "password_hash": _hash_password(credentials.password),
            "role": "student",
            "active": True,
        }
        _local_users_by_email[email] = user
        _local_users_by_id[user["id"]] = user

    return {"message": "Account created. You can now log in."}


@router.post("/login")
async def login(credentials: Credentials, request: Request) -> dict[str, str]:
    email = _normalise_email(credentials.email)
    users = _database_service(request).users
    user = await users.find_one({"email": email}) if users is not None else _local_users_by_email.get(email)

    if user is None or not _verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("active") is False:
        raise HTTPException(status_code=403, detail="This account is inactive")
    role = user.get("role", "student")
    if role not in USER_ROLES:
        logger.error("User %s has an unsupported role", email)
        raise HTTPException(status_code=403, detail="This account has an invalid role")

    return {
        "message": "Login successful",
        "email": email,
        "access_token": _create_access_token(_user_id(user), role),
        "token_type": "bearer",
        "role": role,
    }


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication token validation is not configured",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"]},
        )
        subject = payload["sub"]
    except (jwt.InvalidTokenError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    users = _database_service(request).users
    if users is None:
        user = _local_users_by_id.get(subject)
    else:
        try:
            object_id = ObjectId(subject)
        except InvalidId:
            user = None
        else:
            user = await users.find_one({"_id": object_id})

    if user is None or user.get("active") is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists or is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = user.get("role", "student")
    if role not in USER_ROLES:
        raise HTTPException(status_code=403, detail="This account has an invalid role")
    return _public_user(user)


def require_roles(*roles: str):
    allowed_roles = frozenset(roles)

    async def dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> dict:
        user = await get_current_user(request, credentials)
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


@router.get("/me")
async def current_user(user: dict = Depends(get_current_user)) -> dict:
    return user