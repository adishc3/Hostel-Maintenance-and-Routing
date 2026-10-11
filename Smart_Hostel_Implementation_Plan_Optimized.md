# Smart Hostel Maintenance & Complaint Routing System
## Agent-Optimized Implementation Specification

> **Use this file as the primary build specification.**
>
> Build the system incrementally. Do not redesign the core architecture, replace the ML approach, or add future-scope features unless explicitly requested.
>
> **Important:** Before changing anything in an existing repository, inspect the current repository structure and preserve working code.

---

# 0. Agent Operating Rules

These rules apply to the entire implementation.

1. **Inspect before modifying.**
   - Check the existing repository, package files, environment files, database configuration, and current implementation before creating replacements.
   - Reuse working components where possible.

2. **Work phase-by-phase.**
   - Complete one phase.
   - Run its tests/checks.
   - Fix failures.
   - Only then move to the next phase.

3. **Do not redesign the core architecture.**
   - React + Vite + Tailwind
   - FastAPI + Python
   - MongoDB Atlas
   - NLP + TF-IDF
   - Two Logistic Regression models

4. **Do not replace the ML approach with an LLM, transformer, deep-learning model, or another classifier.**

5. **Do not fabricate results.**
   - Never invent accuracy, F1, predictions, users, complaints, or deployment status.
   - ML metrics must come from actual training/evaluation.

6. **Keep ML and business logic separate.**
   - ML predicts `category` and `priority`.
   - Backend maps `category → department`.
   - ML does not assign individual staff.

7. **Keep security server-side.**
   - JWT authentication.
   - Password hashing.
   - Backend authorization.
   - Frontend route protection is not sufficient.

8. **Do not expose secrets.**
   - MongoDB credentials and JWT secret stay in environment variables.
   - Never send them to the frontend.

9. **Do not silently hide failures.**
   - Log backend/ML failures.
   - Return controlled errors.
   - Never fabricate an ML prediction when prediction fails.

10. **Keep the implementation explainable.**
    - This is an MCA academic project and must be easy to demonstrate and explain in a viva.

11. **Avoid unnecessary scope.**
    - Do not implement image analysis, voice complaints, multilingual NLP, chatbot, IoT, predictive maintenance, notifications, mobile app, or other future enhancements unless explicitly requested.

12. **Do not mark a phase complete without verification.**

---

# 1. Product Definition

## Goal

Build a cloud-based hostel maintenance complaint system that automatically classifies complaints and routes them to the appropriate maintenance department.

## Core workflow

```text
Student
  ↓
React Frontend
  ↓
FastAPI
  ↓
NLP Preprocessing
  ↓
Shared TF-IDF
  ↓
┌─────────────────────┐
│                     │
▼                     ▼
Category Model      Priority Model
│                     │
▼                     ▼
Category             Priority
└──────────┬──────────┘
           ↓
Backend Department Mapping
           ↓
MongoDB Atlas
           ↓
Student / Staff / Admin Dashboards
```

## Primary user roles

| Role | Main responsibilities |
|---|---|
| Student | Submit and track own complaints |
| Staff | View department complaints and update status |
| Admin | System-wide complaints, users and analytics |

---

# 2. Mandatory Technology

## Frontend

- React
- Vite
- Tailwind CSS
- React Router
- Axios
- Context API

## Backend

- Python
- FastAPI
- Pydantic
- PyMongo / MongoDB driver
- JWT
- bcrypt-compatible password hashing

## ML

- Pandas
- NumPy
- scikit-learn
- NLTK or spaCy
- Regex
- Joblib

## Database

- MongoDB Atlas

## Deployment

- Frontend → Vercel
- Backend → Render
- Database → MongoDB Atlas

---

# 3. Architecture Constraints

The frontend must communicate only with FastAPI.

```text
React
  ↓ HTTP/JSON
FastAPI
  ↓
MongoDB Atlas
```

The frontend must never connect directly to MongoDB.

The ML models must run in the backend.

The ML pipeline is:

```text
Complaint
 ↓
Preprocessing
 ↓
TF-IDF
 ↓
Category Logistic Regression
 ↓
Category

Same TF-IDF
 ↓
Priority Logistic Regression
 ↓
Priority
```

Then:

```text
Category
 ↓
Backend mapping
 ↓
Department
```

---

# 4. Initial Repository Structure

Target structure:

```text
smart-hostel/
│
├── frontend/
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── context/
│       ├── hooks/
│       ├── pages/
│       │   ├── student/
│       │   ├── staff/
│       │   └── admin/
│       ├── routes/
│       ├── services/
│       ├── utils/
│       ├── App.jsx
│       └── main.jsx
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── database/
│   │   ├── ml/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── render.yaml
│
├── ml/
│   ├── dataset/
│   ├── models/
│   ├── evaluation/
│   ├── preprocessing.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── ml.md
│
├── .env.example
├── .gitignore
└── README.md
```

Docker Compose may be added for local development but is not required for the core architecture.

---

# 5. Data and ML Specification

## Dataset

Use the project hotel/hostel maintenance complaint dataset.

The documented dataset contains approximately 1,500 complaint records.

Before training:

- Inspect the actual columns.
- Inspect actual category labels.
- Inspect actual priority labels.
- Do not assume labels if the dataset differs.
- Check missing values.
- Remove duplicates.
- Remove empty complaints.
- Inspect class distribution.

Use:

```text
80% training
20% testing
```

Prefer:

```python
random_state=42
```

and stratification where appropriate.

---

# 6. NLP Preprocessing

Create one shared function:

```python
preprocess_text(text)
```

Pipeline:

```text
Raw text
 ↓
Lowercase
 ↓
Regex/text cleaning
 ↓
Tokenization
 ↓
Stop-word removal
 ↓
Lemmatization
 ↓
Processed text
```

The exact same function must be used during:

- training
- evaluation
- production prediction

Do not duplicate preprocessing logic.

---

# 7. TF-IDF

Use exactly one shared TF-IDF vectorizer.

```text
Training text
   ↓
TF-IDF fit
   ↓
TF-IDF vectors
   ├──→ Category model
   └──→ Priority model
```

Save:

```text
tfidf.pkl
```

Do not train separate vectorizers for category and priority.

---

# 8. ML Models

## Category model

```python
LogisticRegression()
```

Input:

```text
TF-IDF vectors
```

Target:

```text
category
```

Save:

```text
category.pkl
```

## Priority model

```python
LogisticRegression()
```

Input:

```text
same TF-IDF vectors
```

Target:

```text
priority
```

Save:

```text
priority.pkl
```

The models are independent but share the same TF-IDF representation.

---

# 9. Expected Labels

Expected categories include:

- Electrical
- Plumbing
- Internet
- Furniture
- Cleaning
- General Maintenance

Expected priorities:

- High
- Medium
- Low

**Important:** Use the actual dataset labels during training. These are project expectations, not permission to hardcode labels that do not exist in the dataset.

---

# 10. ML Evaluation

Evaluate category and priority independently.

Required:

- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Classification Report

Use weighted averages where appropriate for class imbalance.

5-fold cross-validation may be used during evaluation if practical.

Never write expected/fake metrics.

Save:

```text
ml/evaluation/
├── category_report.json
├── priority_report.json
├── category_confusion_matrix.png
└── priority_confusion_matrix.png
```

The project report must use actual generated metrics.

---

# 11. Model Lifecycle

Training is offline.

After training:

```text
category.pkl
priority.pkl
tfidf.pkl
```

FastAPI loads them at startup.

```text
Application startup
 ↓
Load TF-IDF
 ↓
Load category model
 ↓
Load priority model
 ↓
Keep models in memory
```

Do not retrain when a complaint is submitted.

---

# 12. Backend Architecture

FastAPI handles:

- Authentication
- Authorization
- Complaint APIs
- ML prediction
- Department routing
- MongoDB operations
- Dashboard APIs
- Staff APIs
- Admin APIs

Keep route handlers thin.

Business logic belongs in service modules.

Recommended services:

```text
auth_service.py
complaint_service.py
prediction_service.py
dashboard_service.py
database_service.py
```

Required health endpoint:

```http
GET /health
```

Required API documentation:

```text
/docs
```

---

# 13. Database Design

Use MongoDB Atlas.

Collections:

```text
users
complaints
departments
staff
```

## users

```json
{
  "_id": "ObjectId",
  "name": "John",
  "email": "john@example.com",
  "password_hash": "...",
  "role": "student",
  "hostel": "Hostel A",
  "room": "204",
  "created_at": "..."
}
```

Unique index:

```text
email
```

## departments

```json
{
  "_id": "ObjectId",
  "name": "Electrical Maintenance",
  "category": "Electrical",
  "active": true
}
```

## staff

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "department_id": "ObjectId",
  "name": "Staff Member",
  "active": true
}
```

## complaints

```json
{
  "_id": "ObjectId",
  "student_id": "ObjectId",
  "complaint": "The fan in room 204 is not working",
  "category": "Electrical",
  "priority": "Medium",
  "department": "Electrical Maintenance",
  "status": "Pending",
  "assigned_staff_id": null,
  "hostel": "Hostel A",
  "room": "204",
  "created_at": "...",
  "updated_at": "...",
  "resolved_at": null
}
```

Indexes:

```text
student_id
department
status
priority
created_at
department + status
student_id + created_at
```

---

# 14. Department Routing

Department routing is backend business logic.

Initial mapping:

| Category | Department |
|---|---|
| Electrical | Electrical Maintenance |
| Plumbing | Plumbing Maintenance |
| Internet | Network Team |
| Furniture | Carpentry |
| Cleaning | Housekeeping |
| General Maintenance | General Maintenance Team |

Do not train the ML models to predict department.

Do not make department a third ML target.

---

# 15. Authentication

Endpoints:

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

Roles:

```text
student
staff
admin
```

Registration:

```json
{
  "name": "Student Name",
  "email": "student@example.com",
  "password": "password"
}
```

Passwords must be hashed.

Never store or return plain-text passwords.

Login returns:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "name": "...",
    "email": "...",
    "role": "student"
  }
}
```

Create reusable dependencies:

```text
get_current_user()
require_student()
require_staff()
require_admin()
```

---

# 16. Authorization Matrix

| Capability | Student | Staff | Admin |
|---|---:|---:|---:|
| Login | ✓ | ✓ | ✓ |
| Submit complaint | ✓ | - | - |
| View own complaints | ✓ | - | - |
| View department complaints | - | ✓ | ✓ |
| Update complaint status | - | ✓ | ✓ |
| View all complaints | - | - | ✓ |
| View analytics | - | Limited | ✓ |
| View users | - | - | ✓ |
| Delete complaints | - | - | ✓ |

Backend must enforce these permissions.

---

# 17. Complaint API

Implement:

```http
POST   /api/complaints
GET    /api/complaints
GET    /api/complaints/{id}
PUT    /api/complaints/{id}/status
DELETE /api/complaints/{id}
```

Delete is admin-only.

---

# 18. Complaint Creation Pipeline

For:

```http
POST /api/complaints
```

Request:

```json
{
  "complaint": "The fan in room 204 is not working",
  "hostel": "Hostel A",
  "room": "204"
}
```

Execute exactly:

```text
1. Authenticate JWT
2. Validate request
3. Validate complaint text
4. Preprocess text
5. TF-IDF transform
6. Predict category
7. Predict priority
8. Map category → department
9. Create complaint document
10. Store in MongoDB
11. Return result
```

Example response:

```json
{
  "id": "...",
  "complaint": "The fan in room 204 is not working",
  "category": "Electrical",
  "priority": "Medium",
  "department": "Electrical Maintenance",
  "status": "Pending"
}
```

---

# 19. Prediction Service

Create:

```text
backend/app/services/prediction_service.py
```

Responsibilities:

```text
complaint
 ↓
preprocess_text()
 ↓
tfidf.transform()
 ↓
category_model.predict()
 ↓
priority_model.predict()
 ↓
return predictions
```

Optional confidence values may be exposed if derived from the actual model:

```json
{
  "category": "Electrical",
  "category_confidence": 0.94,
  "priority": "Medium",
  "priority_confidence": 0.82
}
```

Do not invent confidence values.

Do not introduce confidence thresholds without evidence from model evaluation.

---

# 20. ML Failure Handling

If prediction fails:

1. Log the exception.
2. Return a controlled error.
3. Do not fabricate a category/priority.
4. Do not silently store a false prediction.
5. Keep the FastAPI process alive.

A General Maintenance/manual-review fallback is future scope, not required for the initial implementation.

---

# 21. Complaint Status

Allowed values:

```text
Pending
In Progress
Resolved
```

Normal flow:

```text
Pending
 ↓
In Progress
 ↓
Resolved
```

When resolved:

```text
resolved_at = current timestamp
```

Always update:

```text
updated_at
```

---

# 22. Dashboard APIs

Implement:

```http
GET /api/dashboard/student
GET /api/dashboard/staff
GET /api/dashboard/admin
```

## Student

Return:

- Total complaints
- Pending
- In Progress
- Resolved
- Own complaint list

## Staff

Return:

- Assigned complaints
- High-priority complaints
- Pending work
- In-progress work
- Resolved count

## Admin

Return:

- Total complaints
- Category statistics
- Priority statistics
- Department workload
- Resolution statistics

---

# 23. Frontend Routes

```text
/login
/register

/student/dashboard
/student/complaints/new
/student/complaints
/student/complaints/:id

/staff/dashboard
/staff/complaints/:id

/admin/dashboard
/admin/complaints
/admin/users
```

---

# 24. Frontend Components

Create reusable components:

```text
Navbar
Sidebar
DashboardCard
ComplaintTable
StatusBadge
PriorityBadge
LoadingSpinner
ProtectedRoute
EmptyState
ErrorMessage
```

Use `AuthContext` for:

```text
currentUser
token
isAuthenticated
loading
```

Use centralized Axios service:

```text
frontend/src/services/api.js
```

Functions:

```text
login()
register()
getCurrentUser()

createComplaint()
getComplaints()
getComplaint()

getStudentDashboard()
getStaffDashboard()
getAdminDashboard()

updateComplaintStatus()
deleteComplaint()
```

Use an Axios interceptor for authentication.

---

# 25. Student UI

## Dashboard

Show:

```text
Total
Pending
In Progress
Resolved
```

Complaint table:

```text
Complaint
Category
Priority
Department
Status
Created Date
Action
```

## New Complaint

Fields:

```text
Complaint Description
Hostel
Room
```

UX:

```text
Submit
 ↓
Loading
 ↓
Prediction
 ↓
Success
```

Show returned:

```text
Category
Priority
Department
Status
```

## Complaint Details

Show:

```text
Complaint ID
Description
Category
Priority
Department
Status
Created At
Updated At
Assigned Staff
```

---

# 26. Staff UI

## Dashboard

Show:

```text
Pending
In Progress
Resolved
High Priority
```

Table:

```text
ID
Complaint
Room
Category
Priority
Status
Created
Action
```

Only show complaints for the staff member's department.

## Complaint Details

Allow:

```text
Pending
In Progress
Resolved
```

Call:

```http
PUT /api/complaints/{id}/status
```

---

# 27. Admin UI

Pages:

```text
/admin/dashboard
/admin/complaints
/admin/users
```

Dashboard:

```text
Total Complaints
Pending
In Progress
Resolved
```

Charts/analytics:

```text
Category Distribution
Priority Distribution
Department Workload
Resolution Statistics
```

Filters:

```text
Category
Priority
Department
Status
Date
```

Sorting:

```text
Newest
Oldest
Highest Priority
```

For larger datasets, filtering should be handled through backend APIs.

---

# 28. Frontend UX

Use Tailwind CSS.

Requirements:

- Clean dashboard.
- Responsive.
- Desktop.
- Laptop.
- Tablet.
- Mobile.
- Consistent cards.
- Clear status badges.
- Clear priority indicators.
- Accessible forms.
- Loading states.
- Empty states.
- Error states.
- Success messages.

Do not communicate important information through color alone.

---

# 29. Error Handling

Frontend messages must be user-friendly.

Example:

```text
Bad:
AxiosError: Request failed with status code 500

Good:
Unable to submit complaint.
Please try again.
```

Handle:

- Invalid login.
- Network failure.
- Server failure.
- Expired session.
- Validation errors.
- Unauthorized access.
- Empty data.

Backend status codes:

```text
200 Success
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
422 Validation Error
500 Internal Server Error
```

---

# 30. Security

Mandatory:

- bcrypt-compatible password hashing.
- JWT authentication.
- Secure JWT secret in environment variables.
- Backend role authorization.
- Backend request validation.
- Production CORS restricted to frontend origin.
- MongoDB credentials never exposed to frontend.
- JWT secret never exposed to frontend.

Environment:

```env
MONGODB_URI=
MONGODB_DATABASE=
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=
FRONTEND_URL=
```

Frontend:

```env
VITE_API_BASE_URL=
```

Create `.env.example`.

Never commit actual secrets.

---

# 31. Testing Strategy

Testing is part of implementation, not a final optional step.

## ML

Test:

- preprocessing
- model loading
- prediction
- evaluation generation

Use representative complaints, but verify outputs from the actual trained model.

## Backend/API

Test:

```text
Register
Login
Invalid login
Current user
Create complaint
Get complaints
Get complaint
Update status
Delete complaint
Dashboard APIs
Role authorization
```

## Security

Verify:

```text
Unauthenticated → protected API = DENY
Student → admin API = DENY
Student → staff API = DENY
Student → another student's complaint = DENY
Staff → other department complaint = DENY
Invalid JWT = DENY
Expired JWT = DENY
Password returned = NEVER
Secret returned = NEVER
```

---

# 32. Primary End-to-End Acceptance Test

This test must pass before the project is considered complete:

```text
1. Student logs in
2. Student submits complaint
3. FastAPI validates it
4. NLP preprocessing runs
5. TF-IDF runs
6. Category prediction runs
7. Priority prediction runs
8. Department mapping runs
9. Complaint is stored in MongoDB
10. Student sees prediction/result
11. Staff logs in
12. Staff sees department complaint
13. Staff changes Pending → In Progress
14. Staff changes In Progress → Resolved
15. Student sees Resolved
16. Admin dashboard reflects the complaint/status
```

---

# 33. Deployment

## MongoDB Atlas

- Create cluster.
- Create database user.
- Configure network access.
- Create database/collections.
- Create indexes.
- Seed departments.
- Configure connection URI.

## Render

Deploy FastAPI.

Verify:

```text
/health
/docs
```

Verify production ML model loading and prediction.

## Vercel

Deploy React/Vite.

Set:

```env
VITE_API_BASE_URL=<Render backend URL>
```

Verify:

- Login.
- Complaint submission.
- ML prediction.
- Student dashboard.
- Staff status updates.
- Admin analytics.

Configure production CORS to allow the Vercel domain.

---

# 34. Seed Department Data

Seed these departments:

```text
Electrical → Electrical Maintenance
Plumbing → Plumbing Maintenance
Internet → Network Team
Furniture → Carpentry
Cleaning → Housekeeping
General Maintenance → General Maintenance Team
```

Use database seed logic rather than duplicating department values throughout the codebase.

---

# 35. Definition of Done

## ML

- [ ] Dataset inspected.
- [ ] Data cleaned.
- [ ] NLP preprocessing implemented.
- [ ] Shared TF-IDF implemented.
- [ ] Category model trained.
- [ ] Priority model trained.
- [ ] Both models evaluated.
- [ ] Actual metrics generated.
- [ ] Confusion matrices generated.
- [ ] Models saved.
- [ ] Models load successfully in FastAPI.

## Backend

- [ ] FastAPI runs.
- [ ] `/health` works.
- [ ] `/docs` works.
- [ ] MongoDB connected.
- [ ] Authentication works.
- [ ] JWT works.
- [ ] Password hashing works.
- [ ] Authorization works.
- [ ] Complaint creation works.
- [ ] Prediction works.
- [ ] Department routing works.
- [ ] Complaint retrieval works.
- [ ] Status update works.
- [ ] Admin deletion works.
- [ ] Dashboard APIs work.
- [ ] Error handling works.
- [ ] Logging works.

## Frontend

- [ ] Login.
- [ ] Registration.
- [ ] Student dashboard.
- [ ] Complaint form.
- [ ] Complaint history.
- [ ] Complaint details.
- [ ] Staff dashboard.
- [ ] Staff complaint details.
- [ ] Admin dashboard.
- [ ] Admin complaints.
- [ ] Admin users.
- [ ] Analytics.
- [ ] Protected routes.
- [ ] Role navigation.
- [ ] Loading states.
- [ ] Error states.
- [ ] Empty states.
- [ ] Responsive UI.

## Database

- [ ] Users.
- [ ] Complaints.
- [ ] Departments.
- [Staff.
- [ ] Unique email index.
- [ ] Complaint indexes.
- [ ] Department seed data.

## Deployment

- [ ] MongoDB Atlas configured.
- [ ] Render backend deployed.
- [ ] Vercel frontend deployed.
- [ ] Environment variables configured.
- [ ] CORS configured.
- [ ] Production API works.
- [ ] Production ML prediction works.
- [ ] End-to-end acceptance test passes.

---

# 36. Implementation Phases

Use this as the execution checklist.

## Phase 0 — Inspect and Plan

- [ ] Inspect repository.
- [ ] Inspect existing frontend/backend.
- [ ] Inspect dataset if present.
- [ ] Identify reusable code.
- [ ] Identify missing pieces.
- [ ] Do not overwrite working functionality unnecessarily.

**Exit condition:** Clear implementation state is known.

---

## Phase 1 — Project Foundation

- [ ] Create/verify frontend.
- [ ] Create/verify backend.
- [ ] Configure dependencies.
- [ ] Configure `.env.example`.
- [ ] Add `/health`.
- [ ] Verify frontend starts.
- [ ] Verify backend starts.

**Exit condition:** Both applications run locally.

---

## Phase 2 — ML

- [ ] Load dataset.
- [ ] Clean dataset.
- [ ] Implement preprocessing.
- [ ] Implement TF-IDF.
- [ ] Train category model.
- [ ] Train priority model.
- [ ] Evaluate both.
- [ ] Save artifacts.

**Exit condition:** A standalone ML prediction script works using saved models.

---

## Phase 3 — Database

- [ ] Connect MongoDB.
- [ ] Create collections/indexes.
- [ ] Seed departments.
- [ ] Verify CRUD.

**Exit condition:** Backend can read/write test records successfully.

---

## Phase 4 — Authentication

- [ ] Registration.
- [ ] Password hashing.
- [ ] Login.
- [ ] JWT.
- [ ] Current user.
- [ ] Role dependencies.

**Exit condition:** Student/staff/admin authentication and authorization work.

---

## Phase 5 — Complaint Backend

- [ ] Complaint schema.
- [ ] Create complaint API.
- [ ] Prediction integration.
- [ ] Department mapping.
- [ ] Complaint retrieval.
- [ ] Complaint details.
- [ ] Status update.
- [ ] Admin delete.

**Exit condition:** Complete backend complaint workflow works through Swagger.

---

## Phase 6 — Student Frontend

- [ ] Login/register.
- [ ] Student dashboard.
- [ ] New complaint.
- [ ] Complaint list.
- [ ] Complaint details.
- [ ] Protected routes.

**Exit condition:** Student can complete the full workflow through the UI.

---

## Phase 7 — Staff Frontend

- [ ] Staff dashboard.
- [ ] Department filtering.
- [ ] Complaint details.
- [ ] Status updates.

**Exit condition:** Staff can process complaints through the UI.

---

## Phase 8 — Admin Frontend

- [ ] Admin dashboard.
- [ ] Analytics.
- [ ] Complaint management.
- [ ] User management.
- [ ] Filters.

**Exit condition:** Admin can monitor the complete system.

---

## Phase 9 — Hardening

- [ ] Validation.
- [ ] Error handling.
- [ ] Logging.
- [ ] Security tests.
- [ ] API tests.
- [ ] ML tests.
- [ ] Responsive UI testing.

**Exit condition:** Local end-to-end acceptance test passes.

---

## Phase 10 — Deployment

- [ ] MongoDB Atlas.
- [ ] Render.
- [ ] Vercel.
- [ ] Environment variables.
- [ ] CORS.
- [ ] Production health check.
- [ ] Production ML prediction.
- [ ] Production end-to-end test.

**Exit condition:** Complete deployed system works.

---

# 37. Agent Progress Protocol

Maintain a lightweight progress file:

```text
docs/IMPLEMENTATION_PROGRESS.md
```

For each phase record:

```markdown
## Phase X — Name

Status: NOT_STARTED | IN_PROGRESS | BLOCKED | COMPLETE

### Completed
- ...

### Tests
- ...

### Issues
- ...

### Decisions
- ...

### Next step
- ...
```

Do not create unnecessary documentation during implementation. Update this file only when the phase status or implementation decisions change.

---

# 38. Agent Completion Report

After each phase, report briefly:

```text
PHASE: <name>
STATUS: COMPLETE / BLOCKED

Implemented:
- ...

Verified:
- ...

Tests:
- ...

Known issues:
- ...

Next phase:
- ...
```

Do not claim completion if tests fail.

If blocked, identify the exact blocker and what information/action is required.

---

# 39. Final Viva Demonstration

The project must support this demonstration:

```text
Student Login
      ↓
Submit:
"The fan in room 204 is not working"
      ↓
NLP
      ↓
TF-IDF
      ↓
Category Model
      ↓
Electrical
      ↓
Priority Model
      ↓
Medium
      ↓
Backend Mapping
      ↓
Electrical Maintenance
      ↓
MongoDB
      ↓
Student sees Pending
      ↓
Electrical Staff logs in
      ↓
Staff sees complaint
      ↓
Pending → In Progress
      ↓
In Progress → Resolved
      ↓
Student sees Resolved
      ↓
Admin dashboard updates
```

This is the minimum complete demonstration.

---

# 40. Final Scope

The completed system must implement:

```text
React
+
FastAPI
+
MongoDB Atlas
+
NLP
+
TF-IDF
+
Category Logistic Regression
+
Priority Logistic Regression
+
Backend Department Routing
+
JWT Authentication
+
Student Dashboard
+
Staff Dashboard
+
Admin Dashboard
+
Testing
+
Cloud Deployment
```

Do not add future enhancements unless explicitly requested.

The final implementation should be production-structured, modular, testable, explainable, and appropriate for an MCA academic project.
