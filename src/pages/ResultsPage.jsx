import { useState } from "react";
import { Button, Card, Field, PageHeading, StatusBadge, selectClass } from "../components/ui.jsx";
import "./ResultsPage.css";

export default function ResultsPage({ cases, navigate }) {
  const requestedCode = new URLSearchParams(window.location.search).get("case");
  const [selectedCode, setSelectedCode] = useState(requestedCode || cases[0]?.code || "");
  const selectedCase = cases.find((item) => item.code === selectedCode) || cases[0];

  return <div className="page results-page">
    <PageHeading page="results" action={<Button variant="secondary" onClick={() => navigate("dashboard")}>← Dashboard</Button>} />
    <Card className="results-card">
      <div className="results-toolbar">
        <Field label="Select a case">
          <select className={selectClass} value={selectedCase?.code || ""} onChange={(event) => {
            setSelectedCode(event.target.value);
            window.history.replaceState({}, "", `/results?case=${encodeURIComponent(event.target.value)}`);
          }} disabled={!cases.length}>
            {cases.map((item) => <option key={item.code} value={item.code}>{item.code}</option>)}
          </select>
        </Field>
        {selectedCase && <StatusBadge status={selectedCase.status} />}
      </div>
      {selectedCase ? <>
        <h2>Case details</h2>
        <dl className="results-details">
          <div><dt>Case code</dt><dd>{selectedCase.code}</dd></div>
          <div><dt>Modality</dt><dd>{selectedCase.modality || "—"}</dd></div>
          <div><dt>Study date</dt><dd>{selectedCase.date || "—"}</dd></div>
          <div><dt>Image file</dt><dd>{selectedCase.fileName || "Not stored for this demo case"}</dd></div>
        </dl>
        {selectedCase.description && <p className="results-description">{selectedCase.description}</p>}
      </> : <div className="results-empty"><p>No cases are available yet.</p><Button onClick={() => navigate("upload")}>Upload an image</Button></div>}
      <div className="results-output">
        <span className="results-label">Model inference unavailable</span>
        <h2>Segmentation output</h2>
        <div className="results-placeholder"><p>No segmentation or metrics are available.</p></div>
        <p className="results-note">This frontend can preview and preprocess images in your browser, but it is not connected to a segmentation model or backend. No medical findings are generated.</p>
      </div>
    </Card>
  </div>;
}
