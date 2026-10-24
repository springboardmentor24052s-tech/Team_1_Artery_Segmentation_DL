import { PAGE_TITLES } from "../data/navigation.js";
import "./ui.css";

export function Button({ children, variant = "primary", className = "", ...props }) {
  return <button className={`button button--${variant} ${className}`} {...props}>{children}</button>;
}

export function Card({ children, className = "", ...props }) {
  return <section className={`card ${className}`} {...props}>{children}</section>;
}

export function Field({ label, children, className = "" }) {
  return <label className={`field ${className}`}><span>{label}</span>{children}</label>;
}

export const inputClass = "form-control";
export const selectClass = "form-control form-control--select";

export function StatusBadge({ status }) {
  const statusClass = {
    Completed: "completed",
    Processing: "processing",
    New: "new",
    Failed: "failed",
  }[status] || "unknown";
  return <span className={`status-badge status-badge--${statusClass}`}><span className="status-badge__dot" />{status}</span>;
}

export function PageHeading({ page, action }) {
  const [title, description] = PAGE_TITLES[page];
  return <div className="page-heading">
    <div><p className="page-heading__eyebrow">Workspace</p><h1>{title}</h1><p className="page-heading__description">{description}</p></div>
    {action}
  </div>;
}

export function Table({ columns, children, empty, className = "" }) {
  return <div className={`table-wrap ${className}`}><table className="data-table">
    <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
    <tbody>{children || <tr><td className="data-table__empty" colSpan={columns.length}>{empty || "No records found."}</td></tr>}</tbody>
  </table></div>;
}
