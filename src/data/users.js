export const USERS_STORAGE_KEY = "stenovision-users";

export const DEFAULT_USERS = [
  { id: "demo-admin", name: "Project Admin", email: "admin@example.com", role: "Admin", status: "Active" },
  { id: "demo-researcher", name: "Research User", email: "researcher@example.com", role: "Researcher", status: "Active" },
  { id: "demo-viewer", name: "Read-only User", email: "viewer@example.com", role: "Viewer", status: "Active" },
];

export function readSavedUsers() {
  try {
    const saved = localStorage.getItem(USERS_STORAGE_KEY);
    if (saved === null) return DEFAULT_USERS;
    const users = JSON.parse(saved);
    if (!Array.isArray(users) || users.some((user) =>
      !user || typeof user.id !== "string" || typeof user.name !== "string" ||
      typeof user.email !== "string" || typeof user.role !== "string"
    )) throw new TypeError("Saved user data is invalid.");
    return users;
  } catch (error) {
    console.error("Could not load saved StenoVision users.", error);
    return DEFAULT_USERS;
  }
}
