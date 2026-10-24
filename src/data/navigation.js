export const NAV_ITEMS = [
  ["dashboard", "Overview", "▦"],
  ["upload", "Image upload", "⇧"],
  ["results", "Results", "⌁"],
  ["users", "User management", "♙"],
];

export const PAGE_TITLES = {
  dashboard: ["Dashboard", "Overview of image analysis and case activity."],
  upload: ["Upload medical image", "Choose a case, select an image, and run local preprocessing."],
  results: ["Analysis results", "Placeholder for segmentation outputs and metrics."],
  users: ["User management", "Static UI preview for future roles and accounts."],
  login: ["Sign in", "Artery Segmentation and Stenosis Detection"],
};

export function pageFromPath(pathname) {
  const segment = pathname.split("/").filter(Boolean).at(-1) || "dashboard";
  const names = {
    "dashboard.html": "dashboard", dashboard: "dashboard",
    "imageupload.html": "upload", upload: "upload",
    "results.html": "results", results: "results",
    "usermanagement.html": "users", users: "users",
    "login.html": "login", login: "login",
  };
  return names[segment.toLowerCase()] || "dashboard";
}
