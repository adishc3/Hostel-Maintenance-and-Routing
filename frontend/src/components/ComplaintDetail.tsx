import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { ArrowLeft, Building2, CalendarDays, MapPin, UserRound, Wrench } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorNotice, Loading } from "./Feedback";
import type { Complaint, ComplaintCategory, ComplaintStatus } from "../types";

const statusOptions: Record<ComplaintStatus, ComplaintStatus[]> = {
  Pending: ["Pending", "In Progress", "Rejected"],
  "In Progress": ["Pending", "In Progress", "Resolved", "Rejected"],
  Resolved: ["In Progress", "Resolved"],
  Rejected: ["Pending", "Rejected"],
};

const allStatuses: ComplaintStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"];
const categories: ComplaintCategory[] = ["Electrical", "Plumbing", "Structural", "General"];
const departmentNames: Record<ComplaintCategory, string> = {
  Electrical: "Electrical Maintenance",
  Plumbing: "Plumbing Maintenance",
  Structural: "Structural Maintenance",
  General: "General Maintenance",
};

export function ComplaintDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [nextStatus, setNextStatus] = useState<ComplaintStatus>("Pending");
  const [note, setNote] = useState("");
  const [staffId, setStaffId] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<ComplaintCategory>("General");
  const [correctionReason, setCorrectionReason] = useState("");
  const [success, setSuccess] = useState(
    typeof location.state?.notice === "string" ? location.state.notice : "",
  );

  async function loadComplaint() {
    setLoading(true);
    setError("");
    try {
      const result = await api.complaint(id);
      setComplaint(result);
      setNextStatus(result.status);
      setSelectedCategory(result.category);
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

  async function reclassify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!complaint) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const result = await api.reclassifyComplaint(complaint.id, {
        category: selectedCategory,
        reason: correctionReason.trim(),
      });
      setComplaint(result);
      setSelectedCategory(result.category);
      setCorrectionReason("");
      setSuccess("Complaint category and department updated.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Category correction failed.");
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
      {error && <ErrorNotice message={error} onRetry={() => void loadComplaint()} />}
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
          <DetailItem icon={<Wrench size={16} />} label="Priority" value={complaint.priority} />
          <DetailItem icon={<CalendarDays size={16} />} label="Submitted" value={new Date(complaint.created_at).toLocaleString()} />
          <DetailItem
            icon={<MapPin size={16} />}
            label="Location"
            value={[complaint.hostel, complaint.room ? `Room ${complaint.room}` : null].filter(Boolean).join(" · ") || "Not provided"}
          />
          <DetailItem icon={<UserRound size={16} />} label="Assigned staff" value={complaint.assigned_staff_id || "Not assigned"} />
        </div>
        {complaint.status_note && (
          <div className="status-note">
            <span className="detail-label">Latest update note</span>
            <p>{complaint.status_note}</p>
          </div>
        )}
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
        <form className="action-panel" onSubmit={reclassify}>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>Correct complaint category</h2>
          <p className="muted-copy">
            The current category is preserved in the record. The server will route the selected category to its active department.
            A department change may clear the current staff assignment.
          </p>
          <div className="inline-fields">
            <label className="field">
              <span>Effective category</span>
              <select
                value={selectedCategory}
                onChange={(event) => setSelectedCategory(event.target.value as ComplaintCategory)}
              >
                {categories.map((category) => <option key={category}>{category}</option>)}
              </select>
              <small className="field-hint">Department preview: {departmentNames[selectedCategory]}</small>
            </label>
            <label className="field">
              <span>Correction reason</span>
              <input
                required
                maxLength={1000}
                value={correctionReason}
                onChange={(event) => setCorrectionReason(event.target.value)}
                placeholder="Explain why the category is incorrect"
              />
            </label>
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? "Updating…" : "Update category"}
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
