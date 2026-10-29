export type UserRole = "student" | "staff" | "admin";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  department_id?: string;
}

export type ComplaintCategory =
  | "Electrical"
  | "Plumbing"
  | "Structural"
  | "General";
export type ComplaintPriority = "High" | "Medium" | "Low";
export type ComplaintStatus = "Pending" | "In Progress" | "Resolved" | "Rejected";

export interface Complaint {
  id: string;
  student_id: string;
  complaint: string;
  category: ComplaintCategory;
  predicted_category: ComplaintCategory;
  priority: ComplaintPriority;
  predicted_priority: ComplaintPriority;
  priority_confidence: number | null;
  category_confidence: number | null;
  department_id: string;
  department: string;
  status: ComplaintStatus;
  status_note: string | null;
  assigned_staff_id: string | null;
  hostel: string | null;
  room: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  reclassification_history: ReclassificationHistoryEntry[];
}

export interface ReclassificationHistoryEntry {
  previous_category: ComplaintCategory;
  new_category: ComplaintCategory;
  previous_department_id: string;
  previous_department: string;
  new_department_id: string;
  new_department: string;
  reason: string;
  admin_id: string;
  timestamp: string;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  limit: number;
  offset: number;
}

export interface ComplaintCreateRequest {
  complaint: string;
  hostel?: string;
  room?: string;
}

export interface ComplaintStatusUpdateRequest {
  status: ComplaintStatus;
  note?: string;
}

export interface ComplaintAssignmentRequest {
  staff_id: string;
}

export interface ComplaintReclassificationRequest {
  category: ComplaintCategory;
  reason: string;
}

export interface LoginResponse {
  message: string;
  email: string;
  access_token: string;
  token_type: "bearer";
  role: UserRole;
}
