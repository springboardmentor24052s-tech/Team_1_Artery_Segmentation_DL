import { Button, Card, PageHeading, Table } from "../components/ui.jsx";
import "./UsersPage.css";

export default function UsersPage() {
  const users = [["Project Admin", "admin@example.com", "Admin"], ["Research User", "researcher@example.com", "Researcher"], ["Read-only User", "viewer@example.com", "Viewer"]];
  const notImplemented = () => window.alert("User management requires backend authentication and is not implemented.");
  return <div className="page users-page"><PageHeading page="users" action={<Button onClick={notImplemented}>+ Add user</Button>} />
    <Card className="users-card"><div className="users-card__header"><h2>User accounts</h2><p>Manage access to the workspace.</p></div><Table columns={["Name", "Email", "Role", "Status", "Action"]}>{users.map(([name, email, role]) => <tr key={email}><td className="user-name-cell">{name}</td><td className="muted-cell">{email}</td><td className="secondary-cell">{role}</td><td><span className="user-active">Active</span></td><td><Button variant="secondary" className="button--small" onClick={notImplemented}>View</Button></td></tr>)}</Table><p className="users-card__note">No real accounts are created by this screen.</p></Card>
  </div>;
}
