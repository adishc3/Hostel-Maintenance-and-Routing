import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { ArrowLeft, Building2, CalendarDays, MapPin, UserRound, Wrench } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorNotice, Loading } from "./Feedback";
import type { Complaint, ComplaintStatus } from "../types";

const statusOptions: Record<ComplaintStatus, ComplaintStatus[]> = {
  Pending: ["Pending", "In Progress", "Rejected"],
  "In Progress": ["Pending", "In Progress", "Resolved", "Rejected"],
  Resolved: ["In Progress", "Resolved"],
  Rejected: ["Pending", "Rejected"],
};

const allStatuses: ComplaintStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"];

export function ComplaintDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [nextStatus, setNextStatus] = useState<ComplaintStatus>("Pending");
  const [note, setNote] = useState("");
  const [staffId, setStaffId] = useState("");
  const [success, setSuccess] = useState("");

  async function loadComplaint() {
    setLoading(true);
    setError("");
    try {
      const result = await api.complaint(id);
      setComplaint(result);
      setNextStatus(result.status);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load this complaint.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadComplaint();
  }, [id]);

  async function saveStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!complaint) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const result = await api.updateStatus(complaint.id, {
        status: nextStatus,
        ...(note.trim() ? { note: note.trim() } : {}),
      });
      setComplaint(result);
      setNextStatus(result.status);
      setNote("");
      setSuccess("Complaint status updated.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Status update failed.");
    } finally {
      setSaving(false);
    }
  }

  async function assignStaff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!complaint) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const result = await api.assignComplaint(complaint.id, { staff_id: staffId.trim() });
      setComplaint(result);
      setStaffId("");
      setSuccess("Staff member assigned.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Assignment failed.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Loading label="Loading complaint…" />;
  if (error && !complaint) return <ErrorNotice message={error} onRetry={() => void loadComplaint()} />;
  if (!complaint) return null;

  const canUpdateStatus = user?.role === "staff" || user?.role === "admin";
  const allowedStatuses = user?.role === "admin" ? allStatuses : statusOptions[complaint.status];

  return (
    <section className="page-content detail-page">
      <button className="back-button" type="button" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} aria-hidden="true" /> Back to complaints
      </button>
      {error && <ErrorNotice message={error} />}
      {success && <p className="success-notice" role="status">{success}</p>}
      <article className="detail-panel">
        <div className="detail-heading">
          <span className={`category-mark category-${complaint.category.toLowerCase()}`}>
            <Wrench size={19} aria-hidden="true" />
          </span>
          <div>
            <p className="eyebrow">COMPLAINT DETAILS</p>
            <h1>{complaint.category} issue</h1>
          </div>
          <span className={`status-pill status-${complaint.status.toLowerCase().replaceAll(" ", "-")}`}>
            {complaint.status}
          </span>
        </div>
        <p className="detail-description">{complaint.complaint}</p>
        <div className="detail-grid">
          <DetailItem icon={<Building2 size={16} />} label="Assigned department" value={complaint.department} />
          <DetailItem icon={<Wrench size={16} />} label="Predicted priority" value={complaint.priority} />
          <DetailItem icon={<CalendarDays size={16} />} label="Submitted" value={new Date(complaint.created_at).toLocaleString()} />
          <DetailItem
            icon={<MapPin size={16} />}
            label="Location"
            value={[complaint.hostel, complaint.room ? `Room ${complaint.room}` : null].filter(Boolean).join(" · ") || "Not provided"}
          />
          <DetailItem icon={<UserRound size={16} />} label="Assigned staff" value={complaint.assigned_staff_id || "Not assigned"} />
          <DetailItem
            icon={<CalendarDays size={16} />}
            label="Model confidence"
            value={`Category ${formatConfidence(complaint.category_confidence)} · Priority ${formatConfidence(complaint.priority_confidence)}`}
          />
        </div>
        <p className="confidence-note">Model confidence is an estimate, not a guarantee of correctness.</p>
      </article>

      {canUpdateStatus && (
        <form className="action-panel" onSubmit={saveStatus}>
          <p className="eyebrow">STAFF ACTION</p>
          <h2>Update status</h2>
          <div className="inline-fields">
            <label className="field">
              <span>New status</span>
              <select value={nextStatus} onChange={(event) => setNextStatus(event.target.value as ComplaintStatus)}>
                {allowedStatuses.map((status) => <option key={status}>{status}</option>)}
              </select>
            </label>
            <label className="field">
              <span>Update note <small>Optional</small></span>
              <input maxLength={1000} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a short update" />
            </label>
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? "Saving…" : "Save status"}
            </button>
          </div>
        </form>
      )}

      {user?.role === "admin" && (
        <form className="action-panel" onSubmit={assignStaff}>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>Assign staff member</h2>
          <p className="muted-copy">Enter an active staff record ID from this complaint’s department.</p>
          <div className="inline-fields assignment-fields">
            <label className="field">
              <span>Staff record ID</span>
              <input
                required
                minLength={24}
                maxLength={24}
                pattern="[0-9a-fA-F]{24}"
                value={staffId}
                onChange={(event) => setStaffId(event.target.value)}
                placeholder="24-character MongoDB ID"
              />
            </label>
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? "Assigning…" : "Assign"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

function DetailItem({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="detail-item">
      <span className="detail-item-icon">{icon}</span>
      <div><span className="detail-label">{label}</span><strong>{value}</strong></div>
    </div>
  );
}

function formatConfidence(value: number | null): string {
  return value === null ? "Unavailable" : `${Math.round(value * 100)}%`;
}
