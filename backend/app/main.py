from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers.auth import router as auth_router
from app.services.database_service import DatabaseService


settings = get_settings()
database_service = DatabaseService(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.database_service = database_service
    await database_service.connect()
    yield
    await database_service.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/health/db")
async def database_health() -> dict[str, str | bool]:
    if not settings.mongodb_uri:
        return {"status": "not_configured", "connected": False}
    connected = await database_service.ping()
    return {"status": "ok" if connected else "unavailable", "connected": connected}


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
