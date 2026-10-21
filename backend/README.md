# Smart Hostel backend

FastAPI service for authentication, complaint routing, and MongoDB persistence.

## Local setup

From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:JWT_SECRET_KEY = (.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
$env:MONGODB_URI = "mongodb+srv://<database-user>:<url-encoded-password>@<cluster-host>/?appName=<app-name>"
$env:MONGODB_DATABASE = "smart_hostel"
$env:BACKEND_CORS_ORIGINS = "http://localhost:5173"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Required backend environment variables:

- `JWT_SECRET_KEY`: a deployment-specific high-entropy secret. Generate one with `secrets.token_urlsafe(48)` as shown above. Never commit it, put it in a frontend variable, or use a shared example value.
- `MONGODB_URI`: the MongoDB connection string.
- `MONGODB_DATABASE`: database name; defaults to `smart_hostel`.
- `BACKEND_CORS_ORIGINS`: comma-separated browser origins; use `http://localhost:5173` for the local Vite frontend.
- `JWT_ACCESS_TOKEN_MINUTES`: positive access-token lifetime; defaults to `60`.

The service fails closed when `JWT_SECRET_KEY` is empty: login and token validation return an explicit `503` configuration error rather than issuing or accepting unsigned tokens. Complaint operations also require a reachable MongoDB database.

## Provisioning staff and administrators

`POST /auth/register` always creates a `student` account. It cannot create staff or administrators. Provision privileged accounts through an authenticated operator or a protected deployment/admin script that:

1. hashes the password with `app.routers.auth._hash_password`;
2. inserts a user with `role` set to `staff` or `admin` and `active: true`;
3. for staff, sets `department_id` to the `_id` of the intended active department;
4. creates the matching active staff record in the `staff` collection with the same department ID.

Do not expose this operation as a public route or accept a client-supplied role during registration. The current admin assignment API accepts a staff MongoDB ID and the server verifies that the staff record is active and belongs to the complaint department.

For local provisioning, use the included script from the repository root. It prompts for the password without printing it:

```powershell
.\.venv\Scripts\python.exe backend\create_user.py --name "Hostel Admin" --email admin@hostel.local --role admin
.\.venv\Scripts\python.exe backend\create_user.py --name "Electrical Staff" --email staff@hostel.local --role staff --department-id <department-object-id>
```

The script reads `MONGODB_URI` and `MONGODB_DATABASE` from the existing environment configuration, rejects duplicate email addresses, and only accepts `admin` or `staff`. Staff provisioning also requires an active department and creates the matching active record in the `staff` collection. To obtain a valid department ID, inspect the active documents in the `departments` collection in MongoDB Compass; use the value of their `_id` field. Never expose this script as a web endpoint or commit credentials.

## Backend checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

The test suite uses mocked database operations for complaint authorization and persistence. A live MongoDB check should only be run against a dedicated test database or with temporary records that are removed afterward.
