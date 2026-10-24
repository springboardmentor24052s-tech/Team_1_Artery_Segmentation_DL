export const STORAGE_KEY = "stenovision-cases";
export const MAX_FILE_SIZE = 15 * 1024 * 1024;

export const DEMO_CASES = [
  { code: "meri marzi 1", modality: "mera man", date: "2026-10-01", status: "Completed" },
  { code: "meri marzi 2", modality: "mera man", date: "2026-10-03", status: "Processing" },
  { code: "meri marzi 3", modality: "mera man", date: "2026-10-05", status: "New" },
  { code: "meri marzi 4", modality: "mera man", date: "2026-10-06", status: "not failed" },
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
