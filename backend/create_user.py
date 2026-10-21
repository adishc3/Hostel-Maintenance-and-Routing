"""Create a privileged Smart Hostel user for local administration.

This script is intentionally not imported by or exposed through FastAPI.
"""

import argparse
import asyncio
import getpass
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import get_settings
from app.routers.auth import Credentials, _hash_password


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a local admin or staff account."
    )
    parser.add_argument("--name", help="Display name for the account")
    parser.add_argument("--email", help="Email address for the account")
    parser.add_argument("--role", choices=("admin", "staff"))
    parser.add_argument(
        "--department-id",
        help="Active department ObjectId (required for staff accounts)",
    )
    return parser.parse_args()


def _prompt(value: str | None, label: str) -> str:
    result = (value or input(f"{label}: ")).strip()
    if not result:
        raise ValueError(f"{label} is required")
    return result


def _password() -> str:
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password:
        raise ValueError("Password is required")
    if password != confirmation:
        raise ValueError("Passwords do not match")
    return password


async def _create_user(arguments: argparse.Namespace) -> None:
    name = _prompt(arguments.name, "Name")
    email = _prompt(arguments.email, "Email").lower()
    role = _prompt(arguments.role, "Role (admin/staff)").lower()
    if role not in {"admin", "staff"}:
        raise ValueError("Role must be admin or staff")
    password = _password()

    try:
        credentials = Credentials(email=email, password=password)
    except ValidationError as exc:
        messages = ", ".join(str(error["msg"]) for error in exc.errors())
        raise ValueError(f"Invalid account details: {messages}") from exc

    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")

    department_id: ObjectId | None = None
    if role == "staff":
        raw_department_id = _prompt(arguments.department_id, "Department ID")
        if not ObjectId.is_valid(raw_department_id):
            raise ValueError("Department ID must be a valid MongoDB ObjectId")
        department_id = ObjectId(raw_department_id)

    client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=3000,
    )
    try:
        await client.admin.command("ping")
        database = client[settings.mongodb_database]
        users = database["users"]

        if await users.find_one({"email": credentials.email}):
            raise ValueError(f"An account with email {credentials.email} already exists")

        if department_id is not None:
            department = await database["departments"].find_one(
                {"_id": department_id, "active": True}
            )
            if department is None:
                raise ValueError(
                    "No active department exists with the supplied department ID"
                )

        now = datetime.now(timezone.utc)
        user = {
            "name": name,
            "email": credentials.email,
            "password_hash": _hash_password(credentials.password),
            "role": role,
            "active": True,
            "created_at": now,
        }
        if department_id is not None:
            user["department_id"] = department_id

        try:
            result = await users.insert_one(user)
        except DuplicateKeyError as exc:
            raise ValueError(
                f"An account with email {credentials.email} already exists"
            ) from exc

        if department_id is not None:
            try:
                await database["staff"].insert_one(
                    {
                        "user_id": result.inserted_id,
                        "name": name,
                        "email": credentials.email,
                        "department_id": department_id,
                        "active": True,
                        "created_at": now,
                    }
                )
            except PyMongoError:
                await users.delete_one({"_id": result.inserted_id})
                raise
    finally:
        client.close()

    print(f"Created {role} account for {credentials.email}.")


def main() -> None:
    try:
        asyncio.run(_create_user(_arguments()))
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
