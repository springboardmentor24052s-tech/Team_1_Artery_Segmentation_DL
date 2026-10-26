import { useState } from "react";
import { Button, Card, Field, PageHeading, selectClass } from "../components/ui.jsx";
import "./AnalysisConfigurationPage.css";

const STORAGE_KEY = "stenovision-analysis-configurations";
const DEFAULT_CONFIGURATION = { grayscale: true, normalize: true, resize: true, outputSize: "512" };

function readConfigurations() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    if (!saved || Array.isArray(saved) || typeof saved !== "object") throw new TypeError("Saved analysis configuration must be an object.");
    return saved;
  } catch (error) {
    console.error("Could not load saved analysis configurations.", error);
    return {};
  }
}

function configurationForCase(code) {
  const saved = readConfigurations()[code];
  if (!saved || typeof saved !== "object") return DEFAULT_CONFIGURATION;
  return {
    grayscale: saved.grayscale === true,
    normalize: saved.normalize === true,
    resize: saved.resize === true,
    outputSize: ["256", "512", "1024"].includes(String(saved.outputSize)) ? String(saved.outputSize) : DEFAULT_CONFIGURATION.outputSize,
  };
}

export default function AnalysisConfigurationPage({ cases, navigate }) {
  const requestedCode = new URLSearchParams(window.location.search).get("case");
  const initialCode = cases.some((item) => item.code === requestedCode) ? requestedCode : cases[0]?.code || "";
  const [selectedCode, setSelectedCode] = useState(initialCode);
  const [configuration, setConfiguration] = useState(() => configurationForCase(initialCode));
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function selectCase(code) {
    setSelectedCode(code);
    setConfiguration(configurationForCase(code));
    setError("");
    setMessage("");
    window.history.replaceState({}, "", `/analysis-configuration?case=${encodeURIComponent(code)}`);
  }

  function saveConfiguration(event) {
    event.preventDefault();
    if (!selectedCode) return;
    try {
      const configurations = readConfigurations();
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...configurations, [selectedCode]: configuration }));
      setError("");
      setMessage("Configuration saved in this browser.");
    } catch (storageError) {
      console.error("Could not save analysis configuration.", storageError);
      setMessage("");
      setError("Could not save configuration in browser storage. Check available storage and try again.");
    }
  }

  return <div className="page analysis-configuration-page">
    <PageHeading page="analysis-configuration" />
    <Card className="analysis-configuration-card">
      {cases.length ? <>
        <Field label="Case"><select className={selectClass} value={selectedCode} onChange={(event) => selectCase(event.target.value)}>{cases.map((item) => <option key={item.code} value={item.code}>{item.code} · {item.modality || "Unknown modality"}</option>)}</select></Field>
        <form onSubmit={saveConfiguration}>
          <h2>Browser preprocessing</h2>
          <p className="configuration-intro">These options describe local image preprocessing only. They do not run a segmentation model or change stored case metadata.</p>
          <div className="configuration-options">
            {[["grayscale", "Convert to grayscale"], ["normalize", "Normalize intensity"], ["resize", "Resize image"]].map(([key, label]) => <label key={key} className="configuration-toggle"><input type="checkbox" checked={configuration[key]} onChange={(event) => setConfiguration((current) => ({ ...current, [key]: event.target.checked }))} />{label}</label>)}
            <Field label="Output size"><select className={selectClass} disabled={!configuration.resize} value={configuration.outputSize} onChange={(event) => setConfiguration((current) => ({ ...current, outputSize: event.target.value }))}>{["256", "512", "1024"].map((size) => <option key={size} value={size}>{size} × {size} px</option>)}</select></Field>
          </div>
          {error && <p role="alert" className="form-message form-message--error">{error}</p>}
          {message && <p role="status" className="form-message form-message--success">{message}</p>}
          <div className="configuration-actions"><Button type="submit" variant="secondary">Save configuration</Button><Button type="button" onClick={() => navigate("upload")}>Go to image upload</Button></div>
        </form>
      </> : <div className="configuration-empty"><p>No cases are available to configure.</p><Button onClick={() => navigate("upload")}>Upload an image</Button></div>}
      <p className="configuration-note">Saved settings are kept in this browser. The app has no backend or inference model.</p>
    </Card>
  </div>;
}
