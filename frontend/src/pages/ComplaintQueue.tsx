import { useCallback, useEffect, useState } from "react";
import { ClipboardList, Filter, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ComplaintCard } from "../components/ComplaintCard";
import { ErrorNotice, Loading } from "../components/Feedback";
import type { Complaint, ComplaintStatus } from "../types";

const statuses: ComplaintStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"];

export function ComplaintQueue() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const isStudent = user?.role === "student";
  const isAdmin = user?.role === "admin";

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = isStudent
        ? await api.myComplaints()
        : await api.complaints(filter ? { status: filter as ComplaintStatus } : {});
      setComplaints(result.items);
      setTotal(result.total);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load complaints.");
    } finally {
      setLoading(false);
    }
  }, [filter, isStudent]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="page-content">
      <div className="page-heading queue-heading">
        <div>
          <p className="eyebrow">{isStudent ? "STUDENT WORKSPACE" : isAdmin ? "ADMIN CONSOLE" : "STAFF WORKSPACE"}</p>
          <h1>{isStudent ? "My complaints" : isAdmin ? "Complaint monitoring" : "Department queue"}</h1>
          <p>{isStudent ? "See every request you’ve submitted and its latest status." : isAdmin ? "Monitor complaint progress across maintenance departments." : "Review and update requests for your authorized department."}</p>
        </div>
        <span className="heading-icon"><ClipboardList size={22} /></span>
      </div>
      <div className="queue-toolbar">
        <span className="results-count">{total} {total === 1 ? "complaint" : "complaints"}</span>
        {!isStudent && (
          <label className="filter-control"><Filter size={15} /><span className="sr-only">Filter complaints by status</span>
            <select value={filter} onChange={(event) => setFilter(event.target.value)}>
              <option value="">All statuses</option>
              {statuses.map((status) => <option key={status}>{status}</option>)}
            </select>
          </label>
        )}
        <button className="icon-button refresh-button" aria-label="Refresh complaints" onClick={() => void load()} type="button"><RefreshCw size={16} /></button>
      </div>
      {error && <ErrorNotice message={error} onRetry={() => void load()} />}
      {loading ? <Loading label="Loading complaints…" /> : complaints.length === 0 ? (
        <div className="empty-state queue-empty"><ClipboardList size={24} /><strong>Nothing to show yet</strong><span>{isStudent ? "Your submitted complaints will appear here." : "There are no complaints matching this view."}</span></div>
      ) : (
        <div className="complaint-list">{complaints.map((complaint) => <ComplaintCard key={complaint.id} complaint={complaint} onSelect={(item) => navigate(`/app/complaints/${item.id}`)} />)}</div>
      )}
      {user?.role === "staff" && <p className="queue-footnote">Results are scoped to your department by the server.</p>}
      {isAdmin && <p className="queue-footnote">Department and status rules remain enforced by the server for every action.</p>}
    </section>
  );
}
