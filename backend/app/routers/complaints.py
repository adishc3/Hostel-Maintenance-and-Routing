import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pymongo import ReturnDocument

from app.routers.auth import get_current_user, require_roles
from app.schemas import (
    ComplaintAssignment,
    ComplaintCreate,
    ComplaintList,
    ComplaintRead,
    ComplaintReclassification,
    ComplaintStatus,
    ComplaintStatusUpdate,
)
from app.services.database_service import DatabaseService
from app.services.prediction_service import PredictionError


router = APIRouter()
logger = logging.getLogger(__name__)

_ALLOWED_TRANSITIONS = {
    ComplaintStatus.PENDING: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.REJECTED},
    ComplaintStatus.IN_PROGRESS: {
        ComplaintStatus.PENDING,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.REJECTED,
    },
    ComplaintStatus.RESOLVED: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.REJECTED: {ComplaintStatus.PENDING},
}


def _database_service(request: Request) -> DatabaseService:
    return request.app.state.database_service


def _object_id(value: str, field_name: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        ) from None


def _require_mongo_database(request: Request):
    database = _database_service(request).database
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is required for complaint operations",
        )
    return database


def _serialize_complaint(document: dict) -> dict:
    history = document.get("reclassification_history", [])
    return {
        "id": str(document["_id"]),
        "student_id": str(document["student_id"]),
        "complaint": document["complaint"],
        "category": document["category"],
        "predicted_category": document.get("predicted_category", document["category"]),
        "priority": document["priority"],
        "predicted_priority": document.get("predicted_priority", document["priority"]),
        "priority_confidence": document.get("priority_confidence"),
        "category_confidence": document.get("category_confidence"),
        "department_id": str(document["department_id"]),
        "department": document["department"],
        "status": document["status"],
        "assigned_staff_id": (
            str(document["assigned_staff_id"])
            if document.get("assigned_staff_id") is not None
            else None
        ),
        "hostel": document.get("hostel"),
        "room": document.get("room"),
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
        "resolved_at": document.get("resolved_at"),
        "reclassification_history": [
            {
                **entry,
                "previous_department_id": str(entry["previous_department_id"]),
                "new_department_id": str(entry["new_department_id"]),
                "admin_id": str(entry["admin_id"]),
            }
            for entry in history
        ],
    }


def _complaint_access_filter(user: dict, document: dict) -> None:
    if user["role"] == "admin":
        return
    if user["role"] == "student" and str(document["student_id"]) == user["id"]:
        return
    if (
        user["role"] == "staff"
        and user.get("department_id") is not None
        and str(document["department_id"]) == user["department_id"]
    ):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


@router.post(
    "",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_complaint(
    payload: ComplaintCreate,
    request: Request,
    user: dict = Depends(require_roles("student")),
) -> dict:
    database = _require_mongo_database(request)
    try:
        prediction = request.app.state.prediction_service.predict(payload.complaint)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PredictionError as exc:
        logger.exception("Prediction service failed while creating complaint")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Complaint prediction is temporarily unavailable",
        ) from exc

    department = await database["departments"].find_one(
        {"category": prediction.category, "active": True}
    )
    if department is None:
        logger.error("No active department configured for category %s", prediction.category)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active department is configured for the predicted category",
        )

    now = datetime.now(timezone.utc)
    student_id = _object_id(user["id"], "authenticated user ID")
    complaint = {
        "student_id": student_id,
        "complaint": payload.complaint,
        "category": prediction.category,
        "predicted_category": prediction.category,
        "priority": prediction.priority,
        "predicted_priority": prediction.priority,
        "category_confidence": prediction.category_confidence,
        "priority_confidence": prediction.priority_confidence,
        "department_id": department["_id"],
        "department": department["name"],
        "status": ComplaintStatus.PENDING.value,
        "assigned_staff_id": None,
        "hostel": payload.hostel,
        "room": payload.room,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None,
        "reclassification_history": [],
    }
    result = await database["complaints"].insert_one(complaint)
    complaint["_id"] = result.inserted_id
    return _serialize_complaint(complaint)


@router.get("/mine", response_model=ComplaintList)
async def list_my_complaints(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("student")),
) -> dict:
    collection = _require_mongo_database(request)["complaints"]
    query = {"student_id": _object_id(user["id"], "authenticated user ID")}
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    return {
        "items": [_serialize_complaint(item) async for item in cursor],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("", response_model=ComplaintList)
async def list_authorized_complaints(
    request: Request,
    department_id: str | None = Query(default=None, min_length=24, max_length=24),
    complaint_status: ComplaintStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("staff", "admin")),
) -> dict:
    collection = _require_mongo_database(request)["complaints"]
    filters: dict = {}
    if user["role"] == "staff":
        staff_department_id = user.get("department_id")
        if staff_department_id is None:
            raise HTTPException(status_code=403, detail="Staff account has no department")
        if department_id and department_id.lower() != staff_department_id.lower():
            raise HTTPException(status_code=403, detail="Staff may only view their department")
        filters["department_id"] = _object_id(staff_department_id, "staff department ID")
    elif department_id:
        filters["department_id"] = _object_id(department_id, "department ID")
    if complaint_status is not None:
        filters["status"] = complaint_status.value

    total = await collection.count_documents(filters)
    cursor = collection.find(filters).sort("created_at", -1).skip(offset).limit(limit)
    return {
        "items": [_serialize_complaint(item) async for item in cursor],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{complaint_id}", response_model=ComplaintRead)
async def get_complaint(
    complaint_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
) -> dict:
    database = _require_mongo_database(request)
    complaint = await database["complaints"].find_one(
        {"_id": _object_id(complaint_id, "complaint ID")}
    )
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _complaint_access_filter(user, complaint)
    return _serialize_complaint(complaint)


@router.patch("/{complaint_id}/status", response_model=ComplaintRead)
async def update_complaint_status(
    complaint_id: str,
    payload: ComplaintStatusUpdate,
    request: Request,
    user: dict = Depends(require_roles("staff", "admin")),
) -> dict:
    database = _require_mongo_database(request)
    complaint_object_id = _object_id(complaint_id, "complaint ID")
    complaints = database["complaints"]
    complaint = await complaints.find_one({"_id": complaint_object_id})
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _complaint_access_filter(user, complaint)

    current_status = ComplaintStatus(complaint["status"])
    if (
        user["role"] != "admin"
        and payload.status not in _ALLOWED_TRANSITIONS[current_status]
        and payload.status != current_status
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot change status from {current_status.value} to {payload.status.value}",
        )
    now = datetime.now(timezone.utc)
    update: dict = {"status": payload.status.value, "updated_at": now}
    if payload.status == ComplaintStatus.RESOLVED:
        update["resolved_at"] = now
    elif current_status == ComplaintStatus.RESOLVED:
        update["resolved_at"] = None
    if payload.note:
        update["status_note"] = payload.note
        update["status_updated_by"] = _object_id(user["id"], "authenticated user ID")

    updated = await complaints.find_one_and_update(
        {"_id": complaint_object_id},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    return _serialize_complaint(updated)


@router.patch(
    "/{complaint_id}/reclassify",
    response_model=ComplaintRead,
)
async def reclassify_complaint(
    complaint_id: str,
    payload: ComplaintReclassification,
    request: Request,
    user: dict = Depends(require_roles("admin")),
) -> dict:
    database = _require_mongo_database(request)
    complaint_object_id = _object_id(complaint_id, "complaint ID")
    complaints = database["complaints"]
    complaint = await complaints.find_one({"_id": complaint_object_id})
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    current_category = complaint.get("category")
    if current_category == payload.category.value:
        return _serialize_complaint(complaint)

    department = await database["departments"].find_one(
        {"category": payload.category.value, "active": True}
    )
    if department is None:
        logger.error("No active department configured for category %s", payload.category.value)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active department is configured for the selected category",
        )

    assigned_staff_id = complaint.get("assigned_staff_id")
    clear_assignment = False
    if assigned_staff_id is not None:
        assigned_staff = await database["staff"].find_one(
            {"_id": assigned_staff_id, "active": True}
        )
        clear_assignment = (
            assigned_staff is None
            or assigned_staff.get("department_id") != department["_id"]
        )

    now = datetime.now(timezone.utc)
    history_entry = {
        "previous_category": current_category,
        "new_category": payload.category.value,
        "previous_department_id": complaint["department_id"],
        "previous_department": complaint["department"],
        "new_department_id": department["_id"],
        "new_department": department["name"],
        "reason": payload.reason,
        "admin_id": _object_id(user["id"], "authenticated user ID"),
        "timestamp": now,
    }
    update = {
        "$set": {
            "category": payload.category.value,
            "department_id": department["_id"],
            "department": department["name"],
            "updated_at": now,
        },
        "$push": {"reclassification_history": history_entry},
    }
    if clear_assignment:
        update["$set"]["assigned_staff_id"] = None

    updated = await complaints.find_one_and_update(
        {"_id": complaint_object_id},
        update,
        return_document=ReturnDocument.AFTER,
    )
    return _serialize_complaint(updated)


@router.put(
    "/{complaint_id}/assignment",
    response_model=ComplaintRead,
    dependencies=[Depends(require_roles("admin"))],
)
async def assign_complaint(
    complaint_id: str,
    payload: ComplaintAssignment,
    request: Request,
) -> dict:
    database = _require_mongo_database(request)
    complaint_object_id = _object_id(complaint_id, "complaint ID")
    staff_object_id = _object_id(payload.staff_id, "staff ID")
    complaints = database["complaints"]
    complaint = await complaints.find_one({"_id": complaint_object_id})
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    staff = await database["staff"].find_one(
        {
            "_id": staff_object_id,
            "department_id": complaint["department_id"],
            "active": True,
        }
    )
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Staff member is inactive or belongs to a different department",
        )
    updated = await complaints.find_one_and_update(
        {"_id": complaint_object_id},
        {
            "$set": {
                "assigned_staff_id": staff_object_id,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    return _serialize_complaint(updated)
