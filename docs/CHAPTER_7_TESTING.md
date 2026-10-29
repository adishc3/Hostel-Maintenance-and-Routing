# Chapter 7 — Testing

## 7.1 Testing Overview

Testing was performed to verify the implemented functionality of the Smart Hostel
Maintenance & Complaint Routing System without changing the frozen machine-learning
artifacts or modifying production records. The scope covered authentication,
role-based permissions, complaint management, ML inference, department routing,
staff assignment, status transitions, administrator reclassification, frontend API
contracts, and application build integrity.

The approach combined:

- Existing backend `unittest` tests with mocked database collections.
- Existing frontend Vitest API-contract tests.
- A production TypeScript/Vite build.
- A non-destructive runtime ML probe using the active artifacts.
- Live backend and MongoDB health checks where the configured Atlas environment
  permitted them.

Tests are classified as Pass, Fail, Blocked, Not Executed, or Not Applicable.
Only executed checks with observed expected results are marked Pass.

## 7.2 Test Environment

The following environment details were verified during this test run:

| Area | Environment |
|---|---|
| Operating system | Windows |
| Backend language | Python 3.13.9 virtual environment at `.venv` |
| Backend framework | FastAPI with Uvicorn |
| Database integration | MongoDB Atlas through Motor/PyMongo |
| Frontend | React, TypeScript, Vite |
| Frontend test tool | Vitest with a browser-like test environment |
| Backend test tool | Python `unittest` and FastAPI `TestClient` |
| ML components | Frozen TF-IDF vectorizer and category/priority classifiers loaded with joblib |
| ML category labels | Electrical, Plumbing, Structural, General |
| ML priority labels | High, Medium, Low |
| Local frontend URL | `http://127.0.0.1:5173` when started |
| Local backend URL | `http://127.0.0.1:8000` when MongoDB startup succeeds |
| Deployment targets | Vercel and Render are documented, but deployed URLs were not supplied for this run |

The backend automated tests use mocked database operations. The active runtime
ML artifacts were loaded from `ml/models` and the stop-word resource from
`ml/resources`.

## 7.3 Functional Testing

### Authentication and authorization

The backend tests verified registration/login compatibility, current-user token
handling, role restrictions, invalid authentication tokens, and protected
complaint access. Public registration creates student accounts; staff and admin
accounts are provisioned separately through the local administrative script.

### Complaint management

The tests verified complaint creation, authenticated student identity, input
validation, ownership restrictions, complaint retrieval, staff department
filtering, status updates, and assignment validation. Complaint creation invokes
the active prediction service before persisting a complaint.

### Machine learning

The active vectorizer and both classifiers loaded successfully in a runtime
probe. Four representative descriptions produced supported category and priority
labels and confidence values. The probe observed the known behavior that
“The power socket is not working in my room.” was classified as `General / High`.
This observation does not establish model accuracy and was not treated as a
backend contract failure.

### Department routing

Backend tests verified that complaint creation stores the predicted category and
the corresponding department ID/name. Administrator reclassification tests
verified server-side category-to-department resolution.

### Staff assignment and status updates

The backend tests verified authorized status updates, valid staff assignment,
rejection of incompatible staff assignment, and department-specific staff access.
The implementation enforces status transitions on the server.

### Administrator reclassification

The tests verified the admin-only reclassification endpoint. The effective
category and department are updated while the original ML category, priority, and
confidence-related values remain distinguishable. Reclassification history stores
the old and new routing values, reason, administrator ID, and timestamp.
Incompatible staff assignments are cleared.

## 7.4 Integration Testing

The mocked backend tests exercised the FastAPI route, authentication dependency,
prediction-service boundary, serialization, and simulated MongoDB persistence
together. The frontend tests exercised the API client request paths, payload
field names, bearer-token attachment, status mutation, assignment, reclassification,
and unauthorized-token cleanup.

The active ML service was integrated with the real local model artifacts and
successfully produced predictions.

Live MongoDB/FastAPI health checks were attempted without creating or modifying
records. They were blocked during application startup because the configured
MongoDB Atlas hosts returned a TLS handshake error:

```text
SSL handshake failed ... tlsv1 alert internal error
```

Consequently, live `/health`, `/health/db`, and `/docs` requests could not be
completed in this run. No deployed Vercel-to-Render test was claimed because
deployed URLs and a confirmed reachable deployment were not available.

## 7.5 Test Cases and Results

The detailed matrix is also available as
[`CHAPTER_7_TEST_CASE_MATRIX.csv`](./CHAPTER_7_TEST_CASE_MATRIX.csv).

| Test ID | Module | Test Scenario | Input / Preconditions | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| B-01 | Authentication | Existing local registration and login | Backend startup test with local user store | Registration and login remain functional | Automated test passed | Pass |
| B-02 | Startup/ML | Prediction service loads once at startup | Frozen artifacts present | Startup loads service successfully | Automated test passed | Pass |
| B-03 | Reclassification | Admin changes category and clears incompatible assignment | Mock complaint assigned to Electrical staff; admin changes to Plumbing | Category/department change, original prediction preserved, assignment cleared | Automated test passed | Pass |
| B-04 | Complaint creation | Stores prediction identity and department | Student submits valid complaint | Prediction, student ID, department and timestamps persist | Automated test passed | Pass |
| B-05 | Validation/security | Empty description and invalid token | Blank complaint; invalid bearer token | Requests rejected with validation/auth errors | Automated test passed | Pass |
| B-06 | Authentication/roles | Login, current user, and role restriction | Student login; staff attempts student-only creation | Login succeeds; staff request rejected | Automated test passed | Pass |
| B-07 | ML failure handling | Prediction/department failures do not create complaints | Mock prediction failure and missing department | Safe error; no complaint persisted | Automated test passed | Pass |
| B-08 | Reclassification security | Non-admin and malformed reclassification requests | Student/staff caller; invalid category; invalid ID | Rejected with role/validation/ID errors | Automated test passed | Pass |
| B-09 | Assignment/status | Staff status update and admin assignment | Authorized staff/admin; incompatible staff record | Valid mutations succeed; incompatible assignment rejected | Automated test passed | Pass |
| B-10 | Ownership/access | Student ownership and staff department scope | Student, outsider, staff, cross-department filter | Owner access succeeds; unauthorized/cross-department access rejected | Automated test passed | Pass |
| B-11 | ML service | Both models accept shared vectorized input | Active vectorizer and classifiers | Shared feature input accepted | Automated test passed | Pass |
| B-12 | ML validation | Empty and invalid complaint text | Empty/non-string inputs | Clear prediction errors | Automated test passed | Pass |
| B-13 | ML artifacts | Missing artifact handling | Missing artifact test fixture | Missing artifact is reported | Automated test passed | Pass |
| B-14 | ML examples | Notebook external examples remain executable | External example inputs | Predictions are returned without assuming correctness | Automated test passed | Pass |
| B-15 | ML error handling | Prediction failure is logged and raised | Model failure fixture | `PredictionError` is raised | Automated test passed | Pass |
| B-16 | ML labels | Representative complaints use supported labels | Representative category/priority inputs | Labels belong to supported sets | Automated test passed | Pass |
| F-01 | Frontend auth | Registration/login API contract | Mocked fetch responses | Correct auth routes, methods and payloads used | Vitest test passed | Pass |
| F-02 | Frontend complaints | Complaint routes and bearer token | Mocked protected requests | Correct complaint fields/routes and Authorization header used | Vitest test passed | Pass |
| F-03 | Frontend mutations | Status, assignment, and reclassification contracts | Mocked mutation responses | Correct PATCH/PUT routes and payloads used | Vitest test passed | Pass |
| F-04 | Frontend session | Unauthorized response handling | Mocked HTTP 401 | Session token is cleared and error is raised | Vitest test passed | Pass |
| ML-01 | Runtime ML | Load active artifacts and predict four descriptions | Real local frozen artifacts | Four predictions use supported labels and expose confidence values | Probe passed; socket example observed as `General / High` | Pass |
| I-01 | Live backend | FastAPI health endpoint | Configured Atlas connection | HTTP 200 health response | Backend exited during MongoDB TLS startup failure | Blocked |
| I-02 | Live database | MongoDB health endpoint | Configured Atlas connection | MongoDB connected response | Could not request endpoint because startup was blocked by TLS handshake failure | Blocked |
| I-03 | Live API docs | OpenAPI endpoint | Backend running | HTTP 200 docs response | Could not request endpoint because startup was blocked by TLS handshake failure | Blocked |

### Automated command results

Backend command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

Observed result:

```text
Ran 16 tests
OK
```

Frontend commands:

```powershell
cd frontend
npm test
npm run build
npm audit
```

Observed results:

```text
1 test file passed
4 tests passed
Production build passed
found 0 vulnerabilities
```

Additional checks:

- `git diff --check` passed.
- Python syntax checks passed for the changed backend files.
- No ML artifact files were changed during this QA run.

## 7.6 Limitations

1. Live MongoDB/FastAPI integration was blocked in this run by the Atlas TLS
   handshake error. The mocked backend suite therefore provides the primary
   route-level evidence for this report.
2. Deployed Vercel-to-Render integration was not executed because deployed URLs
   and a confirmed reachable deployment were not supplied.
3. No browser-based manual role walkthrough was executed in this run.
4. No performance, load, penetration, or long-duration reliability testing was
   performed.
5. The runtime ML probe used representative examples only; it does not measure
   accuracy or replace a held-out evaluation.
6. There is no image-upload functionality in the implemented system, so image
   upload testing is not applicable.
7. The frontend currently stores the bearer token in `sessionStorage`; an
   HttpOnly-cookie migration was outside this project's requested scope.
8. Staff/admin live workflows against MongoDB were not repeated because creating
   temporary live role records was intentionally avoided for this QA run.

## 7.7 Testing Summary

### Test counts

The test-case matrix contains **24 test cases**:

| Result | Count |
|---|---:|
| Passed | 21 |
| Failed | 0 |
| Blocked | 3 |
| Not Executed | 0 |
| Not Applicable | 0 |
| Total | 24 |

The 21 passes comprise 16 backend automated tests, 4 frontend Vitest tests, and
1 runtime ML probe. The 3 blocked cases are the live backend, database-health,
and OpenAPI checks affected by the MongoDB Atlas TLS startup failure.

### Findings and defects

- No automated backend or frontend test failures were observed.
- The ML runtime probe confirmed a known classification limitation for one
  electrical wording example (`General / High`). This was recorded as an ML
  observation and not changed because the active models are frozen.
- Live startup remains dependent on MongoDB Atlas TLS/network availability. This
  is an environment/integration blocker for this run, not a newly diagnosed
  application assertion failure.

### Recommendations

1. Resolve the MongoDB Atlas TLS/network issue and rerun `/health`,
   `/health/db`, and deployed integration checks.
2. Perform manual browser walkthroughs for student, staff, and admin roles using
   dedicated test accounts.
3. Verify Render environment variables and Atlas Network Access from Render.
4. Keep ML accuracy claims tied to the existing evaluation report rather than
   inferring accuracy from examples.
5. Consider a future security review of browser token storage, outside the
   current mini-project scope.

### Conclusion

The automated evidence shows that the implemented authentication, complaint
management, ML inference boundary, department routing, staff operations,
administrator assignment, and administrator reclassification workflows are
functionally covered and passed their existing tests. The frontend API contract
and production build also passed. The only unresolved test execution issue in
this run is the external MongoDB Atlas TLS connection, which prevented live
FastAPI startup and therefore blocked end-to-end deployed verification. Subject
to resolving that environment dependency and completing the recommended manual
browser checks, the system is suitable for demonstration as an MCA mini project.
