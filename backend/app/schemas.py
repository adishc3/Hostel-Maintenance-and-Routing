from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ComplaintCategory(StrEnum):
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    STRUCTURAL = "Structural"
    GENERAL = "General"


class ComplaintPriority(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ComplaintStatus(StrEnum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class ComplaintCreate(BaseModel):
    complaint: str = Field(min_length=1, max_length=5000)
    hostel: str | None = Field(default=None, max_length=120)
    room: str | None = Field(default=None, max_length=40)

    @field_validator("complaint")
    @classmethod
    def complaint_must_have_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Complaint description must not be empty")
        return value

    @field_validator("hostel", "room")
    @classmethod
    def optional_values_must_have_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def note_must_have_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ComplaintAssignment(BaseModel):
    staff_id: str = Field(min_length=24, max_length=24, pattern=r"^[0-9a-fA-F]{24}$")


class ComplaintReclassification(BaseModel):
    category: ComplaintCategory
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def reason_must_have_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Correction reason must not be empty")
        return value


class ReclassificationHistoryEntry(BaseModel):
    previous_category: ComplaintCategory
    new_category: ComplaintCategory
    previous_department_id: str
    previous_department: str
    new_department_id: str
    new_department: str
    reason: str
    admin_id: str
    timestamp: datetime


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    complaint: str
    category: ComplaintCategory
    predicted_category: ComplaintCategory
    priority: ComplaintPriority
    predicted_priority: ComplaintPriority
    priority_confidence: float | None
    category_confidence: float | None
    department_id: str
    department: str
    status: ComplaintStatus
    assigned_staff_id: str | None
    hostel: str | None
    room: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    reclassification_history: list[ReclassificationHistoryEntry]


class ComplaintList(BaseModel):
    items: list[ComplaintRead]
    total: int
    limit: int
    offset: int
