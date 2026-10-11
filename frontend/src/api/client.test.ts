import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, getSessionToken, saveSessionToken } from "./client";

const fetchMock = vi.fn<typeof fetch>();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("backend API contracts", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends registration and login credentials to the existing auth routes", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ message: "Account created." }, 201))
      .mockResolvedValueOnce(jsonResponse({
        message: "Login successful",
        email: "student@example.test",
        access_token: "signed-token",
        token_type: "bearer",
        role: "student",
      }));

    await api.register("student@example.test", "password123");
    await api.login("student@example.test", "password123");

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/auth/register", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ email: "student@example.test", password: "password123" }),
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/auth/login", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ email: "student@example.test", password: "password123" }),
    }));
    expect(new Headers(fetchMock.mock.calls[1][1]?.headers).has("Authorization")).toBe(false);
  });

  it("uses complaint field names and response routes from the backend schemas", async () => {
    saveSessionToken("session-token");
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ id: "complaint-id" }, 201))
      .mockResolvedValueOnce(jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }))
      .mockResolvedValueOnce(jsonResponse({ id: "complaint-id" }));

    await api.createComplaint({
      complaint: "The bathroom tap is leaking.",
      hostel: "North",
      room: "12",
    });
    await api.myComplaints();
    await api.complaint("complaint-id");

    expect(fetchMock.mock.calls[0][0]).toBe("/complaints");
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
      complaint: "The bathroom tap is leaking.",
      hostel: "North",
      room: "12",
    });
    expect(fetchMock.mock.calls[1][0]).toBe("/complaints/mine?limit=50&offset=0");
    expect(fetchMock.mock.calls[2][0]).toBe("/complaints/complaint-id");
    for (const [, init] of fetchMock.mock.calls) {
      expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer session-token");
    }
  });

  it("uses the existing status and assignment mutation contracts", async () => {
    saveSessionToken("session-token");
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ id: "complaint-id", status: "In Progress" }))
      .mockResolvedValueOnce(jsonResponse({ id: "complaint-id", assigned_staff_id: "staff-id" }));

    await api.updateStatus("complaint-id", { status: "In Progress", note: "Started" });
    await api.assignComplaint("complaint-id", { staff_id: "0123456789abcdef01234567" });

    expect(fetchMock.mock.calls[0][0]).toBe("/complaints/complaint-id/status");
    expect(fetchMock.mock.calls[0][1]).toEqual(expect.objectContaining({
      method: "PATCH",
      body: JSON.stringify({ status: "In Progress", note: "Started" }),
    }));
    expect(fetchMock.mock.calls[1][0]).toBe("/complaints/complaint-id/assignment");
    expect(fetchMock.mock.calls[1][1]).toEqual(expect.objectContaining({
      method: "PUT",
      body: JSON.stringify({ staff_id: "0123456789abcdef01234567" }),
    }));
  });

  it("clears the session token on unauthorized protected requests", async () => {
    saveSessionToken("expired-token");
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Invalid or expired authentication token" }, 401));

    await expect(api.currentUser()).rejects.toBeInstanceOf(ApiError);
    expect(getSessionToken()).toBeNull();
  });
});
