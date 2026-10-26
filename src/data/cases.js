export const STORAGE_KEY = "stenovision-cases";
export const MAX_FILE_SIZE = 15 * 1024 * 1024;

export const DEMO_CASES = [
  { code: "ART-001", modality: "CTA", date: "2026-10-01", status: "Completed" },
  { code: "ART-002", modality: "Angiography", date: "2026-10-03", status: "Processing" },
  { code: "ART-003", modality: "MRA", date: "2026-10-05", status: "New" },
  { code: "ART-004", modality: "CTA", date: "2026-10-06", status: "Failed" },
];

export function readSavedCases() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    if (!Array.isArray(saved)) throw new TypeError("Saved case data must be an array.");
    return saved;
  } catch (error) {
    console.error("Could not load saved StenoVision cases.", error);
    return [];
  }
}

export function downloadCasesCsv(cases) {
  const columns = ["Case code", "Modality", "Study date", "Status", "Image file", "Description"];
  const csvCell = (value) => {
    const text = value == null ? "" : String(value);
    const safeText = /^[\s]*[=+\-@]/.test(text) ? `'${text}` : text;
    return `"${safeText.replaceAll('"', '""')}"`;
  };
  const rows = cases.map((item) => [
    item.code,
    item.modality,
    item.date,
    item.status,
    item.fileName,
    item.description,
  ]);
  const csv = [columns, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "stenovision-cases.csv";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
