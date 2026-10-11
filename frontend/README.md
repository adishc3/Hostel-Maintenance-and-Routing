# Smart Hostel frontend

React + Vite client for the FastAPI authentication and complaint APIs.

## Run locally

1. Start the backend from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
   ```

   Configure `JWT_SECRET_KEY` and a reachable MongoDB database in the backend environment before signing in or using complaint operations.

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
