import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app, database_service  # noqa: E402
from app.routers.auth import Credentials, login, register  # noqa: E402
from app.services.prediction_service import PredictionService  # noqa: E402


class AppStartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_loads_prediction_service_once(self) -> None:
        with (
            patch.object(database_service, "connect", new=AsyncMock()),
            patch.object(database_service, "close", new=AsyncMock()),
        ):
            async with app.router.lifespan_context(app):
                prediction_service = app.state.prediction_service
                self.assertIsInstance(prediction_service, PredictionService)
                self.assertIs(app.state.prediction_service, prediction_service)
                self.assertIn(
                    prediction_service.predict("There is a crack in the hallway wall.").category,
                    {"Electrical", "Plumbing", "Structural", "General"},
                )

    async def test_existing_local_register_and_login_still_work(self) -> None:
        class Request:
            app = type(
                "Application",
                (),
                {"state": type("State", (), {"database_service": type("DB", (), {"users": None})()})()},
            )()

        email = "prediction-regression@example.invalid"
        credentials = Credentials(email=email, password="safe-password-123")
        registered = await register(credentials, Request())
        authenticated = await login(credentials, Request())
        self.assertIn("message", registered)
        self.assertEqual(authenticated["email"], email)


if __name__ == "__main__":
    unittest.main()
