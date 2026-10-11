import type {
  Complaint,
  ComplaintAssignmentRequest,
  ComplaintCreateRequest,
  ComplaintListResponse,
  ComplaintStatus,
  ComplaintStatusUpdateRequest,
  LoginResponse,
  User,
} from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
const TOKEN_KEY = "smart-hostel.access-token";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getSessionToken(): string | null {
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function saveSessionToken(token: string): void {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authenticated) {
    const token = getSessionToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Could not reach the server. Check your connection and try again.", 0);
  }

  const rawBody = await response.text();
  let body: unknown;
  if (rawBody) {
    try {
      body = JSON.parse(rawBody) as unknown;
    } catch {
      body = rawBody;
    }
  }

  if (!response.ok) {
    const detail = getErrorMessage(body) ?? `Request failed (${response.status}).`;
    if (response.status === 401 && authenticated) {
      clearSessionToken();
      window.dispatchEvent(new Event("smart-hostel:unauthorized"));
    }
    throw new ApiError(detail, response.status);
  }
  return body as T;
}

function getErrorMessage(body: unknown): string | null {
  if (!body || typeof body !== "object" || !("detail" in body)) return null;
  const detail = body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object" || !("msg" in item)) return "Invalid value";
        return String(item.msg);
      })
      .join(". ");
  }
  return null;
}

export const api = {
  register(email: string, password: string): Promise<{ message: string }> {
    return request(
      "/auth/register",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    );
  },

  login(email: string, password: string): Promise<LoginResponse> {
    return request(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    );
  },

  currentUser(): Promise<User> {
    return request("/auth/me");
  },

  createComplaint(payload: ComplaintCreateRequest): Promise<Complaint> {
    return request("/complaints", { method: "POST", body: JSON.stringify(payload) });
  },

  myComplaints(limit = 50, offset = 0): Promise<ComplaintListResponse> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    return request(`/complaints/mine?${params.toString()}`);
  },

  complaints(filters: { status?: ComplaintStatus; limit?: number; offset?: number } = {}): Promise<ComplaintListResponse> {
    const params = new URLSearchParams();
    if (filters.status) params.set("status", filters.status);
    params.set("limit", String(filters.limit ?? 50));
    params.set("offset", String(filters.offset ?? 0));
    return request(`/complaints?${params.toString()}`);
  },

  complaint(id: string): Promise<Complaint> {
    return request(`/complaints/${encodeURIComponent(id)}`);
  },

  updateStatus(id: string, payload: ComplaintStatusUpdateRequest): Promise<Complaint> {
    return request(`/complaints/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  assignComplaint(id: string, payload: ComplaintAssignmentRequest): Promise<Complaint> {
    return request(`/complaints/${encodeURIComponent(id)}/assignment`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};
