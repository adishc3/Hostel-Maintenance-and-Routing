import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import ReturnDocument


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app import main  # noqa: E402
from app.routers import auth  # noqa: E402
from app.services.prediction_service import PredictionError, PredictionResult  # noqa: E402


JWT_SECRET = "test-only-secret-with-at-least-32-bytes"


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: item[field], reverse=direction < 0)
        return self

    def skip(self, amount):
        self.documents = self.documents[amount:]
        return self

    def limit(self, amount):
        self.documents = self.documents[:amount]
        return self

    def __aiter__(self):
        self._iterator = iter(self.documents)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration from None


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)

    async def find_one(self, query):
        return next(
            (
                item
                for item in self.documents
                if all(item.get(key) == value for key, value in query.items())
            ),
            None,
        )

    async def insert_one(self, document):
        document["_id"] = ObjectId()
        self.documents.append(document)
        return SimpleNamespace(inserted_id=document["_id"])

    async def count_documents(self, query):
        return sum(
            all(item.get(key) == value for key, value in query.items())
            for item in self.documents
        )

    def find(self, query):
        return FakeCursor(
            item
            for item in self.documents
            if all(item.get(key) == value for key, value in query.items())
        )

    async def find_one_and_update(self, query, update, return_document=None):
        document = await self.find_one(query)
        if document is not None:
            before = document.copy()
            document.update(update.get("$set", {}))
            return document if return_document == ReturnDocument.AFTER else before
        return None


class FakeDatabase:
    def __init__(self, collections):
        self.collections = collections

    def __getitem__(self, name):
        return self.collections[name]


class FakeDatabaseService:
    def __init__(self, database, users):
        self.database = database
        self.users = users


class ComplaintApiTests(unittest.TestCase):
    def setUp(self):
        self.student_id = ObjectId()
        self.staff_id = ObjectId()
        self.other_staff_id = ObjectId()
        self.department_id = ObjectId()
        self.other_department_id = ObjectId()
        self.users = FakeCollection(
            [
                {
                    "_id": self.student_id,
                    "email": "student@example.invalid",
                    "password_hash": auth._hash_password("password123"),
                    "role": "student",
                    "active": True,
                },
                {
                    "_id": self.staff_id,
                    "email": "staff@example.invalid",
                    "password_hash": auth._hash_password("password123"),
                    "role": "staff",
                    "department_id": self.department_id,
                    "active": True,
                },
                {
                    "_id": self.other_staff_id,
                    "email": "other-staff@example.invalid",
                    "password_hash": auth._hash_password("password123"),
                    "role": "staff",
                    "department_id": self.other_department_id,
                    "active": True,
                },
                {
                    "_id": ObjectId(),
                    "email": "admin@example.invalid",
                    "password_hash": auth._hash_password("password123"),
                    "role": "admin",
                    "active": True,
                },
            ]
        )
        self.complaints = FakeCollection()
        self.departments = FakeCollection(
            [
                {
                    "_id": self.department_id,
                    "category": "Electrical",
                    "name": "Electrical Maintenance",
                    "active": True,
                }
            ]
        )
        self.staff = FakeCollection(
            [
                {
                    "_id": self.staff_id,
                    "department_id": self.department_id,
                    "active": True,
                },
                {
                    "_id": self.other_staff_id,
                    "department_id": self.other_department_id,
                    "active": True,
                },
            ]
        )
        database = FakeDatabase(
            {
                "users": self.users,
                "complaints": self.complaints,
                "departments": self.departments,
                "staff": self.staff,
            }
        )
        main.app.state.database_service = FakeDatabaseService(database, self.users)
        self.prediction_service = Mock()
        self.prediction_service.predict.return_value = PredictionResult(
            "Electrical", "High", 0.91, 0.88
        )
        main.app.state.prediction_service = self.prediction_service
        self.client = TestClient(main.app)
        self.settings_patch = patch.object(
            auth,
            "get_settings",
            return_value=SimpleNamespace(
                jwt_secret_key=JWT_SECRET,
                jwt_access_token_minutes=60,
            ),
        )
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.addCleanup(self.client.close)

    def token(self, user):
        return auth._create_access_token(str(user["_id"]), user["role"])

    def headers(self, user):
        return {"Authorization": f"Bearer {self.token(user)}"}

    def find_user(self, role, department_id=None):
        return next(
            user
            for user in self.users.documents
            if user["role"] == role
            and user.get("department_id") == department_id
        )

    def create_complaint(self, headers=None):
        return self.client.post(
            "/complaints",
            headers=headers or self.headers(self.find_user("student")),
            json={"complaint": "The power socket is not working."},
        )

    def test_login_current_user_and_role_checks(self):
        response = self.client.post(
            "/auth/login",
            json={"email": "student@example.invalid", "password": "password123"},
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        current = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["id"], str(self.student_id))

        forbidden = self.client.post(
            "/complaints",
            headers=self.headers(self.find_user("staff", self.department_id)),
            json={"complaint": "The power socket is not working."},
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_create_complaint_stores_prediction_identity_and_department(self):
        response = self.create_complaint()
        self.assertEqual(response.status_code, 201, response.text)
        stored = self.complaints.documents[0]
        self.assertEqual(stored["student_id"], self.student_id)
        self.assertEqual(stored["category"], "Electrical")
        self.assertEqual(stored["priority"], "High")
        self.assertEqual(stored["department_id"], self.department_id)
        self.assertEqual(stored["department"], "Electrical Maintenance")
        self.assertEqual(stored["status"], "Pending")
        self.assertIsInstance(stored["created_at"], datetime)
        self.prediction_service.predict.assert_called_once_with(
            "The power socket is not working."
        )

    def test_student_ownership_and_staff_department_scope(self):
        created = self.create_complaint()
        complaint_id = created.json()["id"]
        own = self.client.get(
            f"/complaints/{complaint_id}",
            headers=self.headers(self.find_user("student")),
        )
        self.assertEqual(own.status_code, 200)
        outsider = self.find_user("student")
        outsider["_id"] = ObjectId()
        self.users.documents.append(outsider)
        denied = self.client.get(
            f"/complaints/{complaint_id}", headers=self.headers(outsider)
        )
        self.assertEqual(denied.status_code, 403)

        staff = self.find_user("staff", self.department_id)
        staff_list = self.client.get("/complaints", headers=self.headers(staff))
        self.assertEqual(staff_list.status_code, 200)
        self.assertEqual(staff_list.json()["total"], 1)
        cross_department = self.client.get(
            "/complaints",
            headers=self.headers(staff),
            params={"department_id": str(self.other_department_id)},
        )
        self.assertEqual(cross_department.status_code, 403)

    def test_status_update_and_admin_assignment(self):
        complaint_id = self.create_complaint().json()["id"]
        staff = self.find_user("staff", self.department_id)
        status_response = self.client.patch(
            f"/complaints/{complaint_id}/status",
            headers=self.headers(staff),
            json={"status": "In Progress", "note": "Assigned for repair"},
        )
        self.assertEqual(status_response.status_code, 200, status_response.text)
        self.assertEqual(status_response.json()["status"], "In Progress")

        admin = self.find_user("admin")
        assignment = self.client.put(
            f"/complaints/{complaint_id}/assignment",
            headers=self.headers(admin),
            json={"staff_id": str(self.staff_id)},
        )
        self.assertEqual(assignment.status_code, 200, assignment.text)
        self.assertEqual(assignment.json()["assigned_staff_id"], str(self.staff_id))

        rejected_assignment = self.client.put(
            f"/complaints/{complaint_id}/assignment",
            headers=self.headers(admin),
            json={"staff_id": str(self.other_staff_id)},
        )
        self.assertEqual(rejected_assignment.status_code, 422)

    def test_empty_description_and_invalid_token_are_rejected(self):
        response = self.client.post(
            "/complaints",
            headers=self.headers(self.find_user("student")),
            json={"complaint": " \t "},
        )
        self.assertEqual(response.status_code, 422)
        invalid = self.client.get(
            "/auth/me", headers={"Authorization": "Bearer not-a-valid-token"}
        )
        self.assertEqual(invalid.status_code, 401)

    def test_prediction_and_department_failures_do_not_create_complaints(self):
        self.prediction_service.predict.side_effect = PredictionError("prediction failed")
        unavailable = self.create_complaint()
        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(self.complaints.documents, [])

        self.prediction_service.predict.side_effect = None
        self.departments.documents.clear()
        missing_department = self.create_complaint()
        self.assertEqual(missing_department.status_code, 503)
        self.assertEqual(self.complaints.documents, [])


if __name__ == "__main__":
    unittest.main()
