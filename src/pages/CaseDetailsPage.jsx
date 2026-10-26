import { Button, Card, PageHeading, StatusBadge } from "../components/ui.jsx";
import "./CaseDetailsPage.css";

export default function CaseDetailsPage({ cases, navigate }) {
  const code = new URLSearchParams(window.location.search).get("case");
  const item = cases.find((study) => study.code === code);

  return <div className="page case-details-page">
    <PageHeading page="case-details" action={<Button variant="secondary" onClick={() => navigate("case-management")}>← Case management</Button>} />
    {item ? <Card className="case-details-card">
      <div className="case-details-title"><div><p>Case code</p><h2>{item.code}</h2></div><StatusBadge status={item.status} /></div>
      <dl className="case-details-grid">
        <div><dt>Imaging modality</dt><dd>{item.modality || "—"}</dd></div>
        <div><dt>Study date</dt><dd>{item.date || "—"}</dd></div>
        <div><dt>Image file</dt><dd>{item.fileName || "Not available for this sample case"}</dd></div>
        <div><dt>Storage</dt><dd>{item.fileName ? "Metadata only; source image is not retained" : "Sample data"}</dd></div>
      </dl>
      <div className="case-details-description"><h3>Research notes</h3><p>{item.description || "No notes have been added."}</p></div>
      <div className="case-details-actions">
        <Button variant="secondary" onClick={() => navigate("analysis-configuration", `?case=${encodeURIComponent(item.code)}`)}>Configure analysis</Button>
        <Button onClick={() => navigate("results", `?case=${encodeURIComponent(item.code)}`)}>View results</Button>
      </div>
    </Card> : <Card className="case-details-card case-details-missing">
      <h2>Case not found</h2>
      <p>This case may have been removed from browser storage.</p>
      <Button onClick={() => navigate("case-management")}>Back to case management</Button>
    </Card>}
  </div>;
}
