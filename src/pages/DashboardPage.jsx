import { Button, Card, PageHeading, StatusBadge, Table } from "../components/ui.jsx";
import "./DashboardPage.css";

export default function DashboardPage({ cases, navigate }) {
  const stats = [
    ["Total cases", cases.length, "↗", "All case records"],
    ["Completed", cases.filter((item) => item.status === "Completed").length, "✓", "Analysis complete"],
    ["In progress", cases.filter((item) => item.status === "Processing").length, "◷", "Currently processing"],
    ["New cases", cases.filter((item) => item.status === "New").length, "+", "Ready for review"],
  ];
  return <div className="page dashboard-page">
    <PageHeading page="dashboard" action={<div className="dashboard-actions"><Button variant="secondary" onClick={() => navigate("case-management")}>Manage cases</Button><Button onClick={() => navigate("upload")}><span className="button__plus">+</span> New case</Button></div>} />
    <div className="dashboard-stats">{stats.map(([label, value, icon, note], index) => <Card key={label} className="stat-card">
      <div className="stat-card__top"><p>{label}</p><span className={`stat-card__icon stat-card__icon--${index}`}>{icon}</span></div>
      <p className="stat-card__value">{value}</p><p className="stat-card__note">{note}</p>
    </Card>)}</div>
    <Card className="dashboard-recent"><div className="section-header"><div><h2>Recent cases</h2><p>Latest activity in your workspace</p></div></div>
      <Table columns={["Case code", "Modality", "Status", "Study date", ""]}>{cases.length ? cases.slice(0, 5).map((item) => <tr key={item.code}><td className="case-code-cell">{item.code}</td><td className="secondary-cell">{item.modality}</td><td><StatusBadge status={item.status} /></td><td className="muted-cell">{item.date || "—"}</td><td><Button variant="secondary" className="button--small" onClick={() => navigate("case-details", `?case=${encodeURIComponent(item.code)}`)}>View</Button></td></tr>) : null}</Table>
    </Card>
  </div>;
}
