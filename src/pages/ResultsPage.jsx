import { Button, Card, PageHeading } from "../components/ui.jsx";
import "./ResultsPage.css";

export default function ResultsPage({ navigate }) {
  return <div className="page results-page"><PageHeading page="results" action={<Button variant="secondary" onClick={() => navigate("dashboard")}>← Dashboard</Button>} />
    <Card className="results-card"><span className="results-label">No model result</span><h2>Image visualization</h2><div className="results-placeholder"><p>No model output available yet.</p></div><p className="results-note">No automatic findings are generated in this prototype.</p></Card>
  </div>;
}
