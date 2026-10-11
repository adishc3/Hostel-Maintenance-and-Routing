# Smart Hostel Maintenance & Complaint Routing System
## Complete Implementation Specification for Coding Agent

> **Purpose:** This document is the single implementation specification for building the Smart Hostel Maintenance & Complaint Routing System. Follow the phases and constraints in this document. Do not redesign the core architecture or add out-of-scope features unless explicitly requested.

---

# 1. Project Overview

Build a cloud-based web application for hostel maintenance complaint management.

The system allows:

- Students to register and log in.
- Students to submit maintenance complaints.
- NLP preprocessing of complaint text.
- TF-IDF feature extraction.
- A Logistic Regression model to predict complaint **category**.
- A separate Logistic Regression model to predict complaint **priority**.
- Backend business rules to map predicted category to a maintenance department.
- Storage of complaints in MongoDB Atlas.
- Maintenance staff to view department-specific complaints.
- Staff to update complaint status.
- Students to track complaint progress.
- Administrators to view system-wide complaint analytics.
- Deployment of the frontend on Vercel and backend on Render.

The core ML workflow is:

```text
Complaint
   ↓
NLP Preprocessing
   ↓
TF-IDF
   ↓
 ┌───────────────┬───────────────┐
 ↓               ↓
Category Model   Priority Model
 ↓               ↓
Category         Priority
 └───────┬───────┘
         ↓
Department Mapping
         ↓
MongoDB Atlas
         ↓
Dashboards
```

The ML model predicts only category and priority. It must NOT directly assign individual staff members. Department routing is backend business logic.

---

# 2. Mandatory Technology Stack

Do not replace the core stack.

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
- JWT authentication
- bcrypt-compatible password hashing

## Machine Learning

- Python
- Pandas
- NumPy
- scikit-learn
- NLTK or spaCy
- Regex
- Joblib

## Database

- MongoDB Atlas

## Deployment

- Frontend: Vercel
- Backend: Render
- Database: MongoDB Atlas

---

# 3. Non-Negotiable Architecture

Use this architecture:

```text
                    ┌───────────────────┐
                    │     Student       │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │  React Frontend   │
                    │ Vite + Tailwind   │
                    └─────────┬─────────┘
                              │ REST / Axios
                              ↓
                    ┌───────────────────┐
                    │   FastAPI Backend │
                    │ Auth / APIs       │
                    │ Business Logic    │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │   NLP Pipeline    │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │      TF-IDF       │
                    │ Shared Vectorizer │
                    └─────────┬─────────┘
                              ↓
                  ┌───────────┴───────────┐
                  ↓                       ↓
        ┌──────────────────┐    ┌──────────────────┐
        │ Category Model   │    │ Priority Model   │
        │ Logistic Reg.    │    │ Logistic Reg.    │
        └────────┬─────────┘    └────────┬─────────┘
                 └───────────┬───────────┘
                             ↓
                    ┌───────────────────┐
                    │ Department Mapping│
                    │ Backend Rules     │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │   MongoDB Atlas   │
                    └─────────┬─────────┘
                              ↓
             ┌────────────────┼────────────────┐
             ↓                ↓                ↓
        Student UI        Staff UI         Admin UI
```

The frontend must never connect directly to MongoDB.

The ML models must remain on the backend.

---

# 4. Repository Structure

Create:

```text
smart-hostel/
│
├── frontend/
│
├── backend/
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
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

Docker Compose is optional for local development, but the architecture must remain frontend/backend/database separated.

---

# 5. Development Strategy

Do NOT build the entire system in one step.

Build and verify in phases:

```text
Phase 1  → Project setup
Phase 2  → Dataset + ML preprocessing
Phase 3  → TF-IDF + ML models
Phase 4  → ML evaluation + model saving
Phase 5  → FastAPI foundation
Phase 6  → MongoDB
Phase 7  → Authentication
Phase 8  → Complaint APIs
Phase 9  → ML integration
Phase 10 → Department routing
Phase 11 → Student frontend
Phase 12 → Staff frontend
Phase 13 → Admin frontend
Phase 14 → Testing
Phase 15 → Security hardening
Phase 16 → Deployment
Phase 17 → End-to-end validation
```

After each phase, verify that the implementation works before moving to the next.

---

# 6. PHASE 1 — Project Initialization

## Frontend structure

```text
frontend/
├── src/
│   ├── assets/
│   ├── components/
│   ├── context/
│   ├── hooks/
│   ├── pages/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```

## Backend structure

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── complaints.py
│   │   ├── dashboard.py
│   │   ├── staff.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── complaint_service.py
│   │   ├── prediction_service.py
│   │   ├── dashboard_service.py
│   │   └── database_service.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── complaint.py
│   │   ├── user.py
│   │   └── dashboard.py
│   │
│   ├── auth/
│   │   ├── jwt.py
│   │   ├── dependencies.py
│   │   └── hashing.py
│   │
│   ├── database/
│   │   └── mongodb.py
│   │
│   ├── ml/
│   │   ├── preprocessing.py
│   │   ├── predictor.py
│   │   ├── category.pkl
│   │   ├── priority.pkl
│   │   └── tfidf.pkl
│   │
│   └── utils/
│       └── helpers.py
│
├── requirements.txt
└── render.yaml
```

Keep routers thin. Business logic belongs in services.

---

# 7. PHASE 2 — Dataset and ML Preparation

Use the project complaint dataset.

The documented dataset contains approximately 1,500 hotel maintenance complaint records with complaint text, category, priority and related metadata.

Expected category examples:

- Electrical
- Plumbing
- Internet
- Furniture
- Cleaning
- General Maintenance

Expected priority labels:

- High
- Medium
- Low

Do not assume these labels if the actual dataset differs. Inspect the real dataset first and use its actual labels.

## Data preparation tasks

1. Load dataset.
2. Inspect columns.
3. Check missing values.
4. Remove duplicate complaints.
5. Remove empty complaints.
6. Handle missing labels.
7. Standardize text.
8. Inspect class distribution.
9. Validate labels.
10. Split into training and testing data.

Use an 80/20 train-test split.

Prefer reproducibility with `random_state=42`.

Use stratification where appropriate.

---

# 8. PHASE 3 — NLP Pipeline

Implement one reusable preprocessing function:

```python
preprocess_text(text)
```

Pipeline:

```text
Raw Complaint
     ↓
Lowercase
     ↓
Text Cleaning
     ↓
Tokenization
     ↓
Stop-word Removal
     ↓
Lemmatization
     ↓
Processed Complaint
```

Example:

```text
"The FAN isn't working!!!"
```

may become:

```text
"fan work"
```

The exact same preprocessing code MUST be used for:

- training
- evaluation
- production prediction

Do not create separate preprocessing implementations.

---

# 9. PHASE 4 — TF-IDF

Use one shared TF-IDF vectorizer.

Workflow:

```text
Processed training complaints
            ↓
      TF-IDF.fit_transform()
            ↓
      Shared feature matrix
```

Both models must receive the same TF-IDF representation.

Do NOT create separate vectorizers for category and priority.

Save:

```text
tfidf.pkl
```

---

# 10. PHASE 5 — Category Model

Train:

```python
LogisticRegression()
```

Input:

```text
TF-IDF feature matrix
```

Target:

```text
category
```

Save:

```text
category.pkl
```

The category model answers:

> "What type of maintenance problem is this?"

Example:

```text
"Bathroom tap is leaking"
→ Plumbing
```

---

# 11. PHASE 6 — Priority Model

Train a second independent:

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

The priority model answers:

> "How urgent is this complaint?"

Example:

```text
"Fire in electrical room"
→ High
```

The two models must remain independent.

---

# 12. ML Evaluation

Evaluate Category and Priority models separately.

Required metrics:

- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Classification Report

Use weighted averages when appropriate for imbalanced classes.

Also consider 5-fold cross-validation during model evaluation if practical.

Do NOT hardcode expected accuracy.

Do NOT write fake metrics into the project.

The project report must use the actual results produced by the trained models.

Save evaluation artifacts:

```text
ml/
└── evaluation/
    ├── category_report.json
    ├── priority_report.json
    ├── category_confusion_matrix.png
    └── priority_confusion_matrix.png
```

---

# 13. Model Saving and Loading

Training is offline.

After training:

```text
category.pkl
priority.pkl
tfidf.pkl
```

At FastAPI startup:

```text
load category.pkl
load priority.pkl
load tfidf.pkl
```

Keep the loaded models in memory.

Do NOT retrain models when a student submits a complaint.

---

# 14. PHASE 7 — FastAPI Backend

FastAPI responsibilities:

- Authentication
- Authorization
- Complaint APIs
- ML prediction
- Department routing
- MongoDB CRUD
- Dashboard APIs
- Staff APIs
- Admin APIs

Create:

```http
GET /health
```

It should return a simple healthy response.

FastAPI Swagger documentation must be available at:

```text
/docs
```

---

# 15. PHASE 8 — MongoDB Atlas

Use MongoDB Atlas.

Core collections:

```text
users
complaints
departments
staff
```

A notifications collection may be added later but is not required for the core implementation.

## Users

Example:

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

Create a unique index on `email`.

## Departments

Example:

```json
{
  "_id": "ObjectId",
  "name": "Electrical Maintenance",
  "category": "Electrical",
  "active": true
}
```

## Staff

Example:

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "department_id": "ObjectId",
  "name": "Staff Member",
  "active": true
}
```

## Complaints

Recommended:

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

Create indexes for:

```text
student_id
department
status
priority
created_at
```

Useful compound indexes:

```text
department + status
student_id + created_at
```

---

# 16. Department Mapping

Department mapping must remain backend business logic.

Initial mapping:

| Category | Department |
|---|---|
| Electrical | Electrical Maintenance |
| Plumbing | Plumbing Maintenance |
| Internet | Network Team |
| Furniture | Carpentry |
| Cleaning | Housekeeping |
| General Maintenance | General Maintenance Team |

Do not train the ML model to predict department.

Do not make department assignment part of the ML target.

The architecture is:

```text
Complaint
 ↓
Category Model
 ↓
Electrical
 ↓
Backend mapping
 ↓
Electrical Maintenance
```

---

# 17. PHASE 9 — Authentication

Implement:

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

## Registration

Request:

```json
{
  "name": "Student Name",
  "email": "student@example.com",
  "password": "password"
}
```

Hash the password before storing it.

Never store plain-text passwords.

## Login

Return:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "name": "Student Name",
    "email": "student@example.com",
    "role": "student"
  }
}
```

Use JWT.

Create reusable backend authorization dependencies:

```text
get_current_user()
require_student()
require_staff()
require_admin()
```

---

# 18. Authorization Rules

## Student

Can:

- Submit complaints.
- View own complaints.
- View own complaint details.
- Track status.

Cannot:

- View other students' complaints.
- Access staff APIs.
- Access admin APIs.
- Modify arbitrary complaints.

## Staff

Can:

- View complaints assigned to their department.
- View complaint details.
- Update complaint status.

Cannot:

- Access admin-only functionality.
- Modify complaints outside their department.

## Admin

Can:

- View all complaints.
- View analytics.
- View users.
- Delete complaints.
- Manage system-level information.

Backend authorization is mandatory. Frontend route protection alone is not sufficient.

---

# 19. PHASE 10 — Complaint APIs

Implement:

```http
POST   /api/complaints
GET    /api/complaints
GET    /api/complaints/{id}
PUT    /api/complaints/{id}/status
DELETE /api/complaints/{id}
```

Deletion should be admin-only.

---

# 20. Complaint Creation Workflow

`POST /api/complaints`

Request:

```json
{
  "complaint": "The fan in room 204 is not working",
  "hostel": "Hostel A",
  "room": "204"
}
```

Backend sequence MUST be:

```text
1. Verify JWT
2. Validate request
3. Validate complaint text
4. Preprocess text
5. TF-IDF transform
6. Predict category
7. Predict priority
8. Map category to department
9. Create complaint document
10. Store in MongoDB
11. Return complaint + predictions
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

# 21. Prediction Service

Create:

```text
backend/app/services/prediction_service.py
```

Responsibilities:

```text
preprocess complaint
      ↓
TF-IDF transform
      ↓
category_model.predict()
      ↓
priority_model.predict()
      ↓
return predictions
```

Optionally expose probabilities internally:

```json
{
  "category": "Electrical",
  "category_confidence": 0.94,
  "priority": "Medium",
  "priority_confidence": 0.82
}
```

Do not invent confidence values.

If confidence thresholds are introduced, make them configurable and justify them with actual model evaluation.

---

# 22. ML Failure Handling

If prediction fails:

1. Log the error.
2. Do not silently invent a prediction.
3. Do not corrupt the complaint record.
4. Return a controlled error response.
5. Ensure the FastAPI application remains running.

A future manual-review fallback may route failed predictions to General Maintenance, but this is not mandatory for the first version.

---

# 23. Complaint Status

Allowed states:

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

# 24. Dashboard APIs

Implement:

```http
GET /api/dashboard/student
GET /api/dashboard/staff
GET /api/dashboard/admin
```

## Student dashboard response

Include:

- Total complaints
- Pending
- In Progress
- Resolved
- Complaint list

## Staff dashboard response

Include:

- Assigned complaints
- High-priority complaints
- Pending work
- In-progress work
- Resolved count

## Admin dashboard response

Include:

- Total complaints
- Category statistics
- Priority statistics
- Department workload
- Resolution statistics

---

# 25. PHASE 11 — Student Frontend

Pages:

```text
/login
/register

/student/dashboard
/student/complaints/new
/student/complaints
/student/complaints/:id
```

## Student Dashboard

Show cards:

```text
Total
Pending
In Progress
Resolved
```

Show complaint table:

```text
Complaint
Category
Priority
Department
Status
Created Date
Action
```

Student must only receive their own data from the backend.

---

# 26. Complaint Submission UI

Fields:

```text
Complaint Description
Hostel
Room
```

Validate before API request:

- Complaint cannot be empty.
- Complaint length must be reasonable.
- Required fields must be present.

Submission UX:

```text
Submit
 ↓
Loading spinner
 ↓
Prediction completed
 ↓
Success result
```

Show:

```text
Category
Priority
Department
Status
```

---

# 27. Complaint Details UI

Display:

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

Use a visual status timeline:

```text
Submitted
   ↓
Assigned
   ↓
In Progress
   ↓
Resolved
```

---

# 28. PHASE 12 — Staff Frontend

Pages:

```text
/staff/dashboard
/staff/complaints/:id
```

Dashboard should show:

```text
Pending
In Progress
Resolved
High Priority
```

Complaint table:

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

Staff must only see their department's complaints.

---

# 29. Staff Complaint Details

Show complete complaint information.

Provide status controls:

```text
Pending
In Progress
Resolved
```

Do not allow arbitrary strings.

When staff changes status, call:

```http
PUT /api/complaints/{id}/status
```

---

# 30. PHASE 13 — Admin Frontend

Pages:

```text
/admin/dashboard
/admin/complaints
/admin/users
```

Admin dashboard must contain:

## Summary

```text
Total Complaints
Pending
In Progress
Resolved
```

## Category distribution

```text
Electrical
Plumbing
Internet
Furniture
Cleaning
General Maintenance
```

## Priority distribution

```text
High
Medium
Low
```

## Department workload

```text
Electrical Maintenance
Plumbing Maintenance
Network Team
Carpentry
Housekeeping
General Maintenance
```

## Resolution statistics

Display pending, in-progress and resolved complaints.

Use charts where useful.

---

# 31. Admin Filtering

Implement filters for:

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

Filtering should happen through backend APIs for large datasets rather than downloading everything unnecessarily.

---

# 32. Frontend Architecture

Use reusable components:

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

Use:

```text
AuthContext
```

for:

- current user
- authentication state
- token
- loading state

Use Axios in a centralized API service.

Do not scatter raw Axios calls throughout every component.

---

# 33. Axios

Create:

```text
frontend/src/services/api.js
```

Include functions for:

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

Use an Axios interceptor to attach the JWT.

---

# 34. Protected Routes

Routes:

```text
/login
/register

/student/*
/staff/*
/admin/*
```

Examples:

```text
Student → /admin          = DENY
Student → /staff          = DENY
Staff   → /admin          = DENY
Admin   → /admin          = ALLOW
```

Unauthorized users should be redirected to login.

Wrong-role users should be redirected away from restricted pages.

---

# 35. UI Requirements

Use Tailwind CSS.

The UI should feel like a modern production dashboard rather than a basic college CRUD application.

Requirements:

- Clean layout.
- Responsive design.
- Desktop support.
- Laptop support.
- Tablet support.
- Mobile support.
- Consistent cards.
- Clear status badges.
- Clear priority indicators.
- Accessible forms.
- Loading states.
- Empty states.
- Error states.
- Success messages.

Do not rely on color alone to communicate priority/status.

---

# 36. Error Handling

Frontend should show user-friendly messages.

Examples:

Instead of:

```text
AxiosError: Request failed with status code 500
```

show:

```text
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

Backend must also return predictable HTTP status codes.

Use:

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

# 37. PHASE 14 — Security

Mandatory:

## Password security

Use bcrypt-compatible hashing.

## JWT

Use a secure secret stored in environment variables.

## Database

MongoDB credentials must never be exposed to frontend.

## Frontend

Never expose:

```text
MONGODB_URI
JWT_SECRET
```

## CORS

Production CORS should allow the configured frontend origin.

## Validation

Validate on both frontend and backend.

Frontend validation improves UX.

Backend validation is the security boundary.

---

# 38. Environment Variables

Backend `.env`:

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

Create:

```text
.env.example
```

Never commit actual secrets.

---

# 39. PHASE 15 — Testing

## ML tests

Test preprocessing.

Test model loading.

Test prediction.

Test representative complaints such as:

```text
"The bathroom tap is leaking"
"The Wi-Fi is not working"
"The fan is not working"
```

The exact predicted labels must come from the trained model.

Do not hardcode expected predictions unless they are verified from the actual trained model.

---

# 40. API Tests

Test:

```text
Register
Login
Invalid login
Get current user
Create complaint
Get complaints
Get complaint
Update status
Delete complaint
Student authorization
Staff authorization
Admin authorization
Dashboard APIs
```

---

# 41. Integration Test

The complete workflow must work:

```text
Student Login
      ↓
Submit Complaint
      ↓
FastAPI
      ↓
NLP
      ↓
TF-IDF
      ↓
Category Prediction
      ↓
Priority Prediction
      ↓
Department Mapping
      ↓
MongoDB
      ↓
Student Dashboard
      ↓
Staff Dashboard
      ↓
Staff Status Update
      ↓
MongoDB
      ↓
Student sees updated status
      ↓
Admin dashboard reflects update
```

This is the primary acceptance test.

---

# 42. Security Tests

Verify:

```text
Unauthenticated user cannot access protected APIs.
Student cannot access admin APIs.
Student cannot access staff APIs.
Student cannot read another student's complaint.
Staff cannot modify complaints outside their department.
Passwords are never returned.
JWT secrets are never returned.
Invalid JWT is rejected.
Expired JWT is rejected.
```

---

# 43. PHASE 16 — Deployment

## MongoDB Atlas

1. Create cluster.
2. Create database user.
3. Configure network access.
4. Create database.
5. Create collections.
6. Create indexes.
7. Seed departments.
8. Obtain MongoDB connection URI.

---

# 44. Backend Deployment — Render

Deploy FastAPI backend to Render.

Required:

```text
GitHub
  ↓
Render
  ↓
Install Python dependencies
  ↓
Start FastAPI
  ↓
Load ML models
  ↓
Connect MongoDB Atlas
```

Verify:

```text
/health
/docs
```

Production ML prediction must work.

---

# 45. Frontend Deployment — Vercel

Deploy React/Vite frontend to Vercel.

Set:

```env
VITE_API_BASE_URL=<Render backend URL>
```

Verify:

- Login
- Complaint creation
- ML prediction
- Dashboard loading
- Staff status updates
- Admin analytics

---

# 46. Production CORS

Configure FastAPI CORS using the actual Vercel frontend domain.

Avoid unrestricted production CORS.

---

# 47. Final Project Structure

Target:

```text
smart-hostel/
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── pages/
│   │   │   ├── student/
│   │   │   ├── staff/
│   │   │   └── admin/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
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
├── README.md
└── docker-compose.yml
```

---

# 48. Definition of Done

## Machine Learning

- [ ] Dataset loaded.
- [ ] Dataset inspected.
- [ ] Missing values handled.
- [ ] Duplicate records handled.
- [ ] NLP preprocessing implemented.
- [ ] TF-IDF implemented.
- [ ] Shared vectorizer used.
- [ ] Category Logistic Regression trained.
- [ ] Priority Logistic Regression trained.
- [ ] Category model evaluated.
- [ ] Priority model evaluated.
- [ ] Actual metrics generated.
- [ ] Confusion matrices generated.
- [ ] Models saved.
- [ ] Models load correctly in FastAPI.

## Backend

- [ ] FastAPI running.
- [ ] `/health` works.
- [ ] `/docs` works.
- [ ] MongoDB Atlas connected.
- [ ] Registration works.
- [ ] Login works.
- [ ] JWT works.
- [ ] Password hashing works.
- [ ] Role authorization works.
- [ ] Complaint creation works.
- [ ] NLP prediction works.
- [ ] Category prediction works.
- [ ] Priority prediction works.
- [ ] Department mapping works.
- [ ] Complaint retrieval works.
- [ ] Complaint status updates work.
- [ ] Admin deletion works.
- [ ] Dashboard APIs work.
- [ ] Error handling works.
- [ ] Logging works.

## Frontend

- [ ] Login page.
- [ ] Registration page.
- [ ] Student dashboard.
- [ ] Complaint form.
- [ ] Complaint history.
- [ ] Complaint details.
- [ ] Staff dashboard.
- [ ] Staff complaint details.
- [ ] Admin dashboard.
- [ ] Admin complaint management.
- [ ] Admin user management.
- [ ] Charts/analytics.
- [ ] Protected routes.
- [ ] Role-based navigation.
- [ ] Loading states.
- [ ] Error states.
- [ ] Empty states.
- [ ] Responsive UI.

## Database

- [ ] Users collection.
- [ ] Complaints collection.
- [ ] Departments collection.
- [ ] Staff collection.
- [ ] Unique email index.
- [ ] Complaint indexes.
- [ ] Department seed data.

## Deployment

- [ ] MongoDB Atlas configured.
- [ ] Backend deployed to Render.
- [ ] Frontend deployed to Vercel.
- [ ] Environment variables configured.
- [ ] CORS configured.
- [ ] Production API works.
- [ ] Production ML prediction works.
- [ ] Full end-to-end workflow works.

---

# 49. Critical Agent Rules

These are non-negotiable.

1. Do not redesign the core architecture.
2. Use React + Vite + Tailwind.
3. Use FastAPI + Python.
4. Use MongoDB Atlas.
5. Use TF-IDF.
6. Use two independent Logistic Regression models.
7. Use one shared TF-IDF vectorizer.
8. Train models offline.
9. Load models once at backend startup.
10. Never train during complaint submission.
11. ML predicts category and priority only.
12. Department assignment is backend logic.
13. Never hardcode fake ML accuracy.
14. Always calculate actual evaluation metrics.
15. Never store plain-text passwords.
16. Never expose secrets to the frontend.
17. Enforce authorization on the backend.
18. Students can only access their own complaints.
19. Staff can only access complaints for their department.
20. Admin has system-wide access.
21. Do not silently fabricate ML predictions.
22. Keep routers, services, schemas and ML code modular.
23. Do not add future-scope features to the core implementation.
24. Test every phase before proceeding.
25. Keep the implementation understandable and explainable because this is an MCA academic project and will be used for demonstration and viva.
26. Do not replace the specified ML approach with an LLM or another classifier unless explicitly requested.
27. Do not turn this into a generic hostel-management ERP. The primary purpose is intelligent complaint classification and routing.

---

# 50. Core End-to-End Demonstration

The final application must support this complete scenario:

```text
Student logs in
        ↓
Student submits:
"The fan in room 204 is not working"
        ↓
FastAPI receives complaint
        ↓
NLP preprocessing
        ↓
TF-IDF transformation
        ↓
Category Logistic Regression
        ↓
Electrical
        ↓
Priority Logistic Regression
        ↓
Medium
        ↓
Backend department mapping
        ↓
Electrical Maintenance
        ↓
MongoDB Atlas
        ↓
Student sees:

Category: Electrical
Priority: Medium
Department: Electrical Maintenance
Status: Pending

        ↓
Electrical staff logs in
        ↓
Staff sees complaint
        ↓
Staff changes:

Pending → In Progress
        ↓
Staff resolves complaint
        ↓
In Progress → Resolved
        ↓
Student sees:

Status: Resolved

        ↓
Admin dashboard updates:

Total complaints
Category distribution
Priority distribution
Department workload
Resolution statistics
```

This complete workflow is the minimum successful demonstration of the project.

---

# 51. Final Instruction to the Agent

Build this system phase-by-phase.

At the end of each phase:

1. Run the relevant tests.
2. Verify the implementation.
3. Fix errors before continuing.
4. Keep the code clean and modular.
5. Do not skip validation.
6. Do not create fake data or fake ML metrics.
7. Do not claim a feature is complete until it has been tested.

The final result must be a working, deployable Smart Hostel Maintenance & Complaint Routing System implementing:

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
Department Routing
   +
Student Dashboard
   +
Staff Dashboard
   +
Admin Dashboard
   +
Cloud Deployment
```

The system should be simple enough to explain in an MCA viva while still being structured like a real-world full-stack application.
