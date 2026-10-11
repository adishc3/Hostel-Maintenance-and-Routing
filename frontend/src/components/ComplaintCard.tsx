import { ArrowUpRight, MapPin, Wrench } from "lucide-react";
import type { Complaint } from "../types";

export function ComplaintCard({
  complaint,
  onSelect,
}: {
  complaint: Complaint;
  onSelect: (complaint: Complaint) => void;
}) {
  return (
    <button className="complaint-card" type="button" onClick={() => onSelect(complaint)}>
      <span className={`category-mark category-${complaint.category.toLowerCase()}`}>
        <Wrench size={18} aria-hidden="true" />
      </span>
      <span className="complaint-card-content">
        <span className="complaint-card-top">
          <span className="category-label">{complaint.category}</span>
          <span className={`status-pill status-${complaint.status.toLowerCase().replaceAll(" ", "-")}`}>
            {complaint.status}
          </span>
        </span>
        <span className="complaint-summary">{complaint.complaint}</span>
        <span className="complaint-meta">
          <span>{complaint.department}</span>
          {complaint.room && (
            <span><MapPin size={13} aria-hidden="true" /> Room {complaint.room}</span>
          )}
          <span>{new Date(complaint.created_at).toLocaleDateString()}</span>
        </span>
      </span>
      <ArrowUpRight size={17} aria-hidden="true" className="card-arrow" />
    </button>
  );
}
