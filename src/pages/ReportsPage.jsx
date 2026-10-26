import { Button, Card, PageHeading, StatusBadge, Table } from "../components/ui.jsx";
import { downloadCasesCsv } from "../data/cases.js";
import "./ReportsPage.css";

export default function ReportsPage({ cases }) {
  const completed = cases.filter((item) => item.status === "Completed").length;
  const newCases = cases.filter((item) => item.status === "New").length;
  const failed = cases.filter((item) => item.status === "Failed").length;

  return <div className="page reports-page">
    <PageHeading page="reports" action={<Button variant="secondary" onClick={() => downloadCasesCsv(cases)}>Download CSV</Button>} />
    <div className="reports-stats">
      {[["Cases in workspace", cases.length], ["Completed", completed], ["New", newCases], ["Failed", failed]].map(([label, value]) => <Card key={label} className="report-stat"><span>{label}</span><strong>{value}</strong></Card>)}
    </div>
    <Card className="reports-table-card">
      <div className="reports-table-heading"><div><h2>Case summary</h2><p>Export includes case metadata, not image files or model results.</p></div></div>
      <Table columns={["Case code", "Modality", "Study date", "Status"]} empty="No case data is available to report.">
        {cases.map((item) => <tr key={item.code}><td className="case-code-cell">{item.code}</td><td className="secondary-cell">{item.modality || "—"}</td><td className="muted-cell">{item.date || "—"}</td><td><StatusBadge status={item.status} /></td></tr>)}
      </Table>
      <div className="reports-export"><p>CSV export contains {cases.length} case {cases.length === 1 ? "record" : "records"} and can be opened in spreadsheet software.</p><Button onClick={() => downloadCasesCsv(cases)}>Export case metadata</Button></div>
    </Card>
    <p className="reports-note">This report summarizes demo and browser-local case metadata. It is not a clinical or diagnostic report.</p>
  </div>;
}
