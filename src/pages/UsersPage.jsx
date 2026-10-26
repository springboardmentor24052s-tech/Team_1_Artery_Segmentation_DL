import { useState } from "react";
import { Button, Card, Field, PageHeading, Table, inputClass, selectClass } from "../components/ui.jsx";
import { readSavedUsers, USERS_STORAGE_KEY } from "../data/users.js";
import "./UsersPage.css";

const ROLES = ["Admin", "Researcher", "Viewer"];

export default function UsersPage() {
  const [users, setUsers] = useState(readSavedUsers);
  const [isAdding, setIsAdding] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Researcher");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function saveUsers(updatedUsers) {
    try {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(updatedUsers));
    } catch (storageError) {
      console.error("Could not save StenoVision users.", storageError);
      setError("Could not save changes in browser storage. Check available storage and try again.");
      setMessage("");
      return false;
    }
    setUsers(updatedUsers);
    setError("");
    setMessage("Changes saved in this browser.");
    return true;
  }

  function addUser(event) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Enter a name for this user.");
      setMessage("");
      return;
    }
    const normalizedEmail = email.trim().toLowerCase();
    if (users.some((user) => user.email.toLowerCase() === normalizedEmail)) {
      setError("A user with that email address already exists.");
      setMessage("");
      return;
    }
    const updatedUsers = [...users, {
      id: `user-${Date.now()}`,
      name: name.trim(),
      email: normalizedEmail,
      role,
      status: "Active",
    }];
    if (!saveUsers(updatedUsers)) return;
    setName("");
    setEmail("");
    setRole("Researcher");
    setIsAdding(false);
  }

  function updateUser(id, changes) {
    saveUsers(users.map((user) => user.id === id ? { ...user, ...changes } : user));
  }

  function removeUser(user) {
    if (!window.confirm(`Remove ${user.name} from this local demo workspace?`)) return;
    saveUsers(users.filter((item) => item.id !== user.id));
  }

  return <div className="page users-page">
    <PageHeading page="users" action={<Button onClick={() => { setIsAdding(!isAdding); setError(""); }}>{isAdding ? "Cancel" : "+ Add user"}</Button>} />
    {isAdding && <Card className="users-add-card">
      <h2>Add a demo user</h2>
      <form className="users-add-form" onSubmit={addUser}>
        <Field label="Full name"><input className={inputClass} value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required /></Field>
        <Field label="Email address"><input className={inputClass} type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></Field>
        <Field label="Role"><select className={selectClass} value={role} onChange={(event) => setRole(event.target.value)}>{ROLES.map((item) => <option key={item}>{item}</option>)}</select></Field>
        <Button type="submit">Add user</Button>
      </form>
    </Card>}
    <Card className="users-card">
      <div className="users-card__header"><h2>User accounts</h2><p>Manage accounts for this browser demo. These are not real application credentials.</p></div>
      <Table columns={["Name", "Email", "Role", "Status", "Action"]} empty="No users found.">
        {users.map((user) => <tr key={user.id}>
          <td className="user-name-cell">{user.name}</td>
          <td className="muted-cell">{user.email}</td>
          <td><select className="user-role-select" aria-label={`Role for ${user.name}`} value={user.role} onChange={(event) => updateUser(user.id, { role: event.target.value })}>{ROLES.map((item) => <option key={item}>{item}</option>)}</select></td>
          <td><button className={`user-status${user.status === "Active" ? "" : " user-status--inactive"}`} onClick={() => updateUser(user.id, { status: user.status === "Active" ? "Inactive" : "Active" })}>{user.status || "Active"}</button></td>
          <td><Button variant="danger" className="button--small" onClick={() => removeUser(user)}>Remove</Button></td>
        </tr>)}
      </Table>
      {error && <p role="alert" className="form-message form-message--error users-message">{error}</p>}
      {message && <p role="status" className="form-message form-message--success users-message">{message}</p>}
      <p className="users-card__note">User changes are stored locally and do not create accounts on a server.</p>
    </Card>
  </div>;
}
