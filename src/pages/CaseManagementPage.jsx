import { useMemo, useState } from "react";
import { Button, Card, Field, PageHeading, StatusBadge, Table, inputClass, selectClass } from "../components/ui.jsx";
import { DEMO_CASES } from "../data/cases.js";
import "./CaseManagementPage.css";

const STATUSES = ["All statuses", "New", "Processing", "Completed", "Failed"];

export default function CaseManagementPage({ cases, onRemove, navigate }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [error, setError] = useState("");
  const filteredCases = useMemo(() => cases.filter((item) => {
    const matchesSearch = `${item.code} ${item.modality || ""} ${item.fileName || ""}`.toLowerCase().includes(search.trim().toLowerCase());
    return matchesSearch && (status === "All statuses" || item.status === status);
  }), [cases, search, status]);

  function removeCase(item) {
    if (DEMO_CASES.some((demoCase) => demoCase.code === item.code)) return;
    if (!window.confirm(`Delete local case ${item.code}? This only removes its metadata from this browser.`)) return;
    const result = onRemove(item.code);
    setError(result);
  }

  return <div className="page case-management-page">
    <PageHeading page="case-management" action={<Button onClick={() => navigate("upload")}>+ New case</Button>} />
    <Card className="case-management-card">
      <div className="case-management-filters">
        <Field label="Search cases"><input className={inputClass} type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search code, modality, or file" /></Field>
        <Field label="Filter by status"><select className={selectClass} value={status} onChange={(event) => setStatus(event.target.value)}>{STATUSES.map((item) => <option key={item}>{item}</option>)}</select></Field>
      </div>
      {error && <p role="alert" className="form-message form-message--error case-management-message">{error}</p>}
      <Table columns={["Case code", "Modality", "Study date", "Status", "Actions"]} empty="No cases match your search.">
        {filteredCases.map((item) => {
          const isDemo = DEMO_CASES.some((demoCase) => demoCase.code === item.code);
          return <tr key={item.code}>
            <td className="case-code-cell">{item.code}</td>
            <td className="secondary-cell">{item.modality || "—"}</td>
            <td className="muted-cell">{item.date || "—"}</td>
            <td><StatusBadge status={item.status} /></td>
            <td className="case-management-actions">
              <Button variant="secondary" className="button--small" onClick={() => navigate("case-details", `?case=${encodeURIComponent(item.code)}`)}>Details</Button>
              <Button variant="danger" className="button--small" disabled={isDemo} title={isDemo ? "Sample cases cannot be removed" : "Remove local case"} onClick={() => removeCase(item)}>Delete</Button>
            </td>
          </tr>;
        })}
      </Table>
      <p className="case-management-note">Sample cases are read-only. Deleting a locally saved case removes its metadata from this browser; image files are not stored.</p>
    </Card>
  </div>;
}
