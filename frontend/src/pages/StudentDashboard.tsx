import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ArrowRight, ClipboardList, Plus, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { ComplaintCard } from "../components/ComplaintCard";
import { ErrorNotice, Loading } from "../components/Feedback";
import type { Complaint, ComplaintCreateRequest } from "../types";

export function StudentDashboard() {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [description, setDescription] = useState("");
  const [hostel, setHostel] = useState("");
  const [room, setRoom] = useState("");

  const loadComplaints = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.myComplaints();
      setComplaints(result.items);
      setTotal(result.total);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load your complaints.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadComplaints();
  }, [loadComplaints]);

  async function submitComplaint(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    const payload: ComplaintCreateRequest = {
      complaint: description.trim(),
      ...(hostel.trim() ? { hostel: hostel.trim() } : {}),
      ...(room.trim() ? { room: room.trim() } : {}),
    };
    try {
      const created = await api.createComplaint(payload);
      setDescription("");
      setHostel("");
      setRoom("");
      setSuccess("Your complaint has been submitted and routed to the maintenance team.");
      await loadComplaints();
      navigate(`/app/complaints/${created.id}`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not submit your complaint.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-content">
      <div className="page-heading">
        <div><p className="eyebrow">STUDENT WORKSPACE</p><h1>Your space, taken care of.</h1><p>Tell us what needs attention. We’ll route it to the right team.</p></div>
        <span className="heading-icon"><Sparkles size={22} /></span>
      </div>
      {error && <ErrorNotice message={error} onRetry={() => void loadComplaints()} />}
      {success && <p className="success-notice" role="status">{success}</p>}
      <div className="student-grid">
        <form className="form-panel" onSubmit={submitComplaint}>
          <div className="panel-title"><span className="section-icon"><Plus size={17} /></span><div><p className="eyebrow">NEW REQUEST</p><h2>Report a problem</h2></div></div>
          <label className="field">
            <span>What needs fixing?</span>
            <textarea required minLength={1} maxLength={5000} rows={5} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe what happened and where you noticed it…" />
            <small className="field-hint">Up to 5,000 characters. Please include useful details.</small>
          </label>
          <div className="inline-fields">
            <label className="field"><span>Hostel <small>Optional</small></span><input maxLength={120} value={hostel} onChange={(event) => setHostel(event.target.value)} placeholder="Hostel or building name" /></label>
            <label className="field"><span>Room <small>Optional</small></span><input maxLength={40} value={room} onChange={(event) => setRoom(event.target.value)} placeholder="Room number" /></label>
          </div>
          <button className="button button-primary submit-complaint" type="submit" disabled={saving || !description.trim()}>
            {saving ? "Submitting…" : "Submit complaint"} {!saving && <ArrowRight size={17} />}
          </button>
          <p className="prediction-hint">Category and priority are predicted automatically after submission.</p>
        </form>
        <aside className="how-panel">
          <p className="eyebrow">WHAT HAPPENS NEXT</p><h2>From report to repair.</h2>
          <ol className="steps">
            <li><span>01</span><div><strong>Tell us the details</strong><small>A clear description helps us understand the issue.</small></div></li>
            <li><span>02</span><div><strong>We route it for you</strong><small>Your report is classified and sent to a maintenance department.</small></div></li>
            <li><span>03</span><div><strong>Follow the progress</strong><small>Check updates any time in My complaints.</small></div></li>
          </ol>
        </aside>
      </div>
      <div className="list-section">
        <div className="section-heading"><div><p className="eyebrow">YOUR REQUESTS</p><h2>Recent complaints <span className="count-badge">{total}</span></h2></div><button className="link-button" type="button" onClick={() => navigate("/app/complaints")}>View all <ArrowRight size={15} /></button></div>
        {loading ? <Loading label="Loading your complaints…" /> : complaints.length === 0 ? (
          <div className="empty-state"><ClipboardList size={24} /><strong>No complaints yet</strong><span>When you submit a maintenance request, it will show up here.</span></div>
        ) : (
          <div className="complaint-list">{complaints.slice(0, 3).map((complaint) => <ComplaintCard key={complaint.id} complaint={complaint} onSelect={(item) => navigate(`/app/complaints/${item.id}`)} />)}</div>
        )}
      </div>
    </section>
  );
}
