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
  priority: ComplaintPriority;
  priority_confidence: number | null;
  category_confidence: number | null;
  department_id: string;
  department: string;
  status: ComplaintStatus;
  assigned_staff_id: string | null;
  hostel: string | null;
  room: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
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

export interface LoginResponse {
  message: string;
  email: string;
  access_token: string;
  token_type: "bearer";
  role: UserRole;
}
