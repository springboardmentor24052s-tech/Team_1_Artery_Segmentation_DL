export const NAV_ITEMS = [
  ["dashboard", "Overview", "▦"],
  ["case-management", "Case management", "▤"],
  ["upload", "Image upload", "⇧"],
  ["analysis-configuration", "Analysis setup", "⚙"],
  ["results", "Results", "⌁"],
  ["reports", "Reports", "▥"],
  ["users", "User management", "♙"],
];

export const PAGE_TITLES = {
  dashboard: ["Dashboard", "Overview of image analysis and case activity."],
  "case-management": ["Case management", "Find, review, and manage study cases."],
  upload: ["Upload medical image", "Choose a case, select an image, and run local preprocessing."],
  "analysis-configuration": ["Analysis configuration", "Choose local preprocessing options for a selected case."],
  results: ["Analysis results", "Review case details and available analysis output."],
  "case-details": ["Case details", "Review metadata for the selected study case."],
  reports: ["Reports", "Review workspace activity and export case metadata."],
  users: ["User management", "Manage demo workspace accounts stored in this browser."],
  login: ["Sign in", "Artery Segmentation and Stenosis Detection"],
};

export function pageFromPath(pathname) {
  const segment = pathname.split("/").filter(Boolean).at(-1) || "dashboard";
  const names = {
    "dashboard.html": "dashboard", dashboard: "dashboard",
    "case-management": "case-management", cases: "case-management",
    "imageupload.html": "upload", upload: "upload",
    "analysis-configuration": "analysis-configuration", configuration: "analysis-configuration",
    "results.html": "results", results: "results",
    "case-details": "case-details", "case-details.html": "case-details",
    reports: "reports",
    "usermanagement.html": "users", users: "users",
    "login.html": "login", login: "login",
  };
  return names[segment.toLowerCase()] || "dashboard";
}
