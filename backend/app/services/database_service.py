import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings


logger = logging.getLogger(__name__)

CATEGORY_DEPARTMENT_NAMES = {
    "Electrical": "Electrical Maintenance",
    "Plumbing": "Plumbing Maintenance",
    "Structural": "Structural Maintenance",
    "General": "General Maintenance",
}


class DatabaseService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    @property
    def database(self) -> AsyncIOMotorDatabase | None:
        return self._database

    @property
    def users(self):
        if self._database is None:
            return None
        return self._database["users"]

    @property
    def complaints(self):
        if self._database is None:
            return None
        return self._database["complaints"]

    @property
    def departments(self):
        if self._database is None:
            return None
        return self._database["departments"]

    @property
    def staff(self):
        if self._database is None:
            return None
        return self._database["staff"]

    async def connect(self) -> None:
        if not self._settings.mongodb_uri:
            return
        client = AsyncIOMotorClient(self._settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        try:
            await client.admin.command("ping")
            database = client[self._settings.mongodb_database]
            await self._initialize_schema(database)
        except Exception:
            client.close()
            logger.exception("Unable to connect to MongoDB or initialize its schema")
            raise
        self._client = client
        self._database = database

    async def _initialize_schema(self, database: AsyncIOMotorDatabase) -> None:
        collection_names = await database.list_collection_names()
        for name in ("users", "complaints", "departments", "staff"):
            if name not in collection_names:
                await database.create_collection(name)

        await database["users"].create_index("email", unique=True)

        complaints = database["complaints"]
        for field in ("student_id", "department", "status", "priority", "created_at"):
            await complaints.create_index(field)
        await complaints.create_index("department_id")
        await complaints.create_index("assigned_staff_id")
        await complaints.create_index([("department", 1), ("status", 1)])
        await complaints.create_index([("student_id", 1), ("created_at", 1)])
        await database["departments"].create_index("category", unique=True)
        await database["departments"].create_index("name", unique=True)

        for category, name in CATEGORY_DEPARTMENT_NAMES.items():
            await database["departments"].update_one(
                {"category": category},
                {
                    "$set": {"name": name, "active": True},
                    "$setOnInsert": {"category": category},
                },
                upsert=True,
            )

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
        except Exception:
            return False
        return True

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
