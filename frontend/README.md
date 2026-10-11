# Smart Hostel frontend

React + Vite client for the FastAPI authentication and complaint APIs.

## Run locally

1. Configure and start the backend from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   $env:JWT_SECRET_KEY = (.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
   $env:MONGODB_URI = "mongodb+srv://<database-user>:<url-encoded-password>@<cluster-host>/?appName=<app-name>"
   $env:MONGODB_DATABASE = "smart_hostel"
   $env:BACKEND_CORS_ORIGINS = "http://localhost:5173"
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
   ```

   `JWT_SECRET_KEY` must be a private, high-entropy value. Generate it with the shown `secrets.token_urlsafe(48)` command; never commit it or expose it to Vite. The backend fails safely with an explicit `503` when the secret is missing. See [backend/README.md](../backend/README.md) for the privileged-account provisioning process.

2. In another terminal, install and start the frontend:

   ```powershell
   cd frontend
   Copy-Item .env.example .env
   npm install
   npm run dev
   ```

   Open the Vite URL printed in the terminal (normally `http://localhost:5173`). With `VITE_API_BASE_URL` empty, Vite proxies `/auth` and `/complaints` to the development target in `VITE_API_PROXY_TARGET` (default `http://localhost:8000`).

For a separately hosted API, set `VITE_API_BASE_URL` to its base URL at build time and configure the backend CORS allowlist for the frontend origin. Do not commit production environment values.

## Checks

```powershell
npm test
npm run build
```

The login response returns a bearer JWT, and `/auth/me` is used to validate the session and determine the current role. The token is kept in `sessionStorage`, cleared on logout or an unauthorized response, and never stored in persistent `localStorage`. Since the backend currently returns the JWT in JSON rather than an HttpOnly cookie, JavaScript running on the page can access the session token; an HttpOnly cookie/refresh-token contract would be needed to eliminate that exposure.

The admin assignment API accepts a staff MongoDB record ID, but the backend currently exposes no staff-directory endpoint. The admin assignment form therefore accepts the staff record ID directly and lets the server validate that the account is active and belongs to the complaint's department.
