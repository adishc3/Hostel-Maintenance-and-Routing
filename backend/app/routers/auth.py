from hashlib import pbkdf2_hmac
from secrets import token_bytes

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.database_service import DatabaseService


router = APIRouter()
_local_users: dict[str, dict[str, str]] = {}


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
    salt_hex, digest_hex = stored_hash.split("$", maxsplit=1)
    expected = _hash_password(password, bytes.fromhex(salt_hex)).split("$", maxsplit=1)[1]
    return expected == digest_hex


def _database_service(request: Request) -> DatabaseService:
    return request.app.state.database_service


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(credentials: Credentials, request: Request) -> dict[str, str]:
    email = _normalise_email(credentials.email)
    users = _database_service(request).users

    if users is not None:
        if await users.find_one({"email": email}):
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        await users.insert_one({"email": email, "password_hash": _hash_password(credentials.password)})
    else:
        if email in _local_users:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        _local_users[email] = {"password_hash": _hash_password(credentials.password)}

    return {"message": "Account created. You can now log in."}


@router.post("/login")
async def login(credentials: Credentials, request: Request) -> dict[str, str]:
    email = _normalise_email(credentials.email)
    users = _database_service(request).users
    user = await users.find_one({"email": email}) if users is not None else _local_users.get(email)

    if user is None or not _verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful", "email": email}