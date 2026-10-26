import { useEffect, useState } from "react";
import { MAX_FILE_SIZE } from "../data/cases.js";
import { Button, Card, Field, PageHeading, inputClass, selectClass } from "../components/ui.jsx";
import "./UploadPage.css";

export default function UploadPage({ cases, onSave }) {
  const [code, setCode] = useState("");
  const [modality, setModality] = useState("Angiography");
  const [studyDate, setStudyDate] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [originalUrl, setOriginalUrl] = useState("");
  const [processedUrl, setProcessedUrl] = useState("");
  const [dimensions, setDimensions] = useState("");
  const [processedDimensions, setProcessedDimensions] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [gray, setGray] = useState(true);
  const [normalize, setNormalize] = useState(true);
  const [resize, setResize] = useState(true);
  const [size, setSize] = useState(512);

  useEffect(() => () => {
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    if (processedUrl) URL.revokeObjectURL(processedUrl);
  }, [originalUrl, processedUrl]);

  function chooseFile(selected) {
    setError("");
    setMessage("");
    if (!selected) return;
    const allowed = ["image/png", "image/jpeg", "image/webp", "image/bmp"];
    if (!allowed.includes(selected.type) && !/\.(png|jpe?g|webp|bmp)$/i.test(selected.name)) {
      setError("Unsupported format. Choose PNG, JPG/JPEG, WEBP, or BMP. DICOM/NIfTI are not supported.");
      return;
    }
    if (!selected.size) { setError("The file is empty."); return; }
    if (selected.size > MAX_FILE_SIZE) { setError("File exceeds the 15 MB limit."); return; }
    const url = URL.createObjectURL(selected);
    const image = new Image();
    image.onload = () => {
      setFile(selected);
      setOriginalUrl(url);
      setProcessedUrl("");
      setDimensions(`${image.naturalWidth} × ${image.naturalHeight} px`);
      setProcessedDimensions("");
    };
    image.onerror = () => { URL.revokeObjectURL(url); setError("The browser could not decode this image."); };
    image.src = url;
  }

  function processImage() {
    if (!file || !originalUrl) return;
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = resize ? Number(size) : image.naturalWidth;
      canvas.height = resize ? Number(size) : image.naturalHeight;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) { setError("Canvas processing is unavailable."); return; }
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
      const data = pixels.data;
      let low = 255;
      let high = 0;
      for (let index = 0; index < data.length; index += 4) {
        if (gray) {
          const value = Math.round(0.299 * data[index] + 0.587 * data[index + 1] + 0.114 * data[index + 2]);
          data[index] = data[index + 1] = data[index + 2] = value;
        }
        low = Math.min(low, data[index], data[index + 1], data[index + 2]);
        high = Math.max(high, data[index], data[index + 1], data[index + 2]);
      }
      if (normalize && high > low) {
        for (let index = 0; index < data.length; index += 4) {
          data[index] = Math.round((data[index] - low) * 255 / (high - low));
          data[index + 1] = Math.round((data[index + 1] - low) * 255 / (high - low));
          data[index + 2] = Math.round((data[index + 2] - low) * 255 / (high - low));
        }
      }
      context.putImageData(pixels, 0, 0);
      canvas.toBlob((blob) => {
        if (!blob) { setError("Could not create processed output."); return; }
        setProcessedUrl(URL.createObjectURL(blob));
        setProcessedDimensions(`${canvas.width} × ${canvas.height} px`);
        setError("");
      }, "image/png");
    };
    image.onerror = () => setError("The browser could not decode this image.");
    image.src = originalUrl;
  }

  function clearForm() {
    setCode(""); setDescription(""); setFile(null); setOriginalUrl(""); setProcessedUrl("");
    setDimensions(""); setProcessedDimensions(""); setError(""); setMessage("");
    const input = document.getElementById("image-file-input");
    if (input) input.value = "";
  }

  function saveCase() {
    const normalizedCode = code.trim();
    if (!file) { setError("Choose an image before saving the case."); return; }
    if (!normalizedCode) { setError("Enter a case code first."); return; }
    if (cases.some((item) => typeof item.code === "string" && item.code.toLowerCase() === normalizedCode.toLowerCase())) { setError("That case code already exists."); return; }
    const result = onSave({
      code: normalizedCode,
      modality,
      date: studyDate || new Date().toISOString().slice(0, 10),
      status: "New",
      fileName: file.name,
      description,
    });
    if (result) { setError(result); return; }
    setError("");
    setMessage("Case metadata saved in this browser.");
  }

  const fileSize = file ? file.size < 1048576 ? `${(file.size / 1024).toFixed(1)} KB` : `${(file.size / 1048576).toFixed(2)} MB` : "";
  return <div className="page upload-page">
    <PageHeading page="upload" action={<span className="local-demo-badge">Local demo</span>} />
    <Card className="upload-info-card"><h2 className="card-title">Case information</h2>
      <div className="upload-info-grid">
        <Field label="Case code"><input className={inputClass} value={code} onChange={(event) => setCode(event.target.value)} placeholder="e.g. CASE-005" /></Field>
        <Field label="Imaging modality"><select className={selectClass} value={modality} onChange={(event) => setModality(event.target.value)}>{["Angiography", "CTA", "MRA", "Other"].map((item) => <option key={item}>{item}</option>)}</select></Field>
        <Field label="Study date"><input className={inputClass} type="date" value={studyDate} onChange={(event) => setStudyDate(event.target.value)} /></Field>
      </div>
      <Field label="Image description" className="upload-description-field"><textarea className={`${inputClass} form-control--textarea`} rows="3" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Optional research notes; do not enter identifying patient details." /></Field>
    </Card>
    <Card className="upload-file-card">
      <div className="upload-file-heading"><div><h2>Medical image file</h2><p>PNG, JPG/JPEG, WEBP, BMP · Maximum 15 MB</p></div><span>STEP 01</span></div>
      <label htmlFor="image-file-input" onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); chooseFile(event.dataTransfer.files[0]); }}
        className={`upload-dropzone${isDragging ? " upload-dropzone--active" : ""}`}>
        <input id="image-file-input" className="visually-hidden" type="file" accept="image/png,image/jpeg,image/webp,image/bmp,.png,.jpg,.jpeg,.webp,.bmp" onChange={(event) => chooseFile(event.target.files?.[0])} />
        <span className="upload-dropzone__icon">↑</span>
        <span className="upload-dropzone__title">Drag and drop an image here</span><span className="upload-dropzone__browse">or <strong>browse files</strong></span>
        <span className="upload-dropzone__note">The file stays on this device in this version.</span>
      </label>
      {file && <div className="upload-file-summary"><span className="upload-file-summary__icon">IMG</span><div><p>{file.name}</p><small>{fileSize} · {dimensions}</small></div><Button variant="danger" className="button--small" onClick={() => { setFile(null); setOriginalUrl(""); setProcessedUrl(""); setDimensions(""); setProcessedDimensions(""); }}>Remove</Button></div>}
      {error && <p role="alert" className="form-message form-message--error">{error}</p>}
      {message && <p role="status" className="form-message form-message--success">{message}</p>}
      <div className="upload-previews">
        {[["Original image", originalUrl, dimensions, "Preview appears here."], ["Preprocessed image", processedUrl, processedDimensions, "Run preprocessing to see output."]].map(([label, src, dims, empty]) => <div className="upload-preview" key={label}><p>{label}</p><div className="upload-preview__frame">{src ? <img src={src} alt={label} /> : <span>{empty}</span>}</div><small>Dimensions: {dims || "—"}</small></div>)}
      </div>
      <h3 className="upload-options-title">Preprocessing options</h3>
      <div className="upload-options">
        {[["Convert to grayscale", gray, setGray], ["Normalize intensity", normalize, setNormalize], ["Resize image", resize, setResize]].map(([label, checked, setter]) => <label key={label} className="upload-toggle"><input type="checkbox" checked={checked} onChange={(event) => setter(event.target.checked)} />{label}</label>)}
        <Field label="Output size"><select className={selectClass} value={size} disabled={!resize} onChange={(event) => setSize(event.target.value)}>{[256, 512, 1024].map((item) => <option key={item}>{item}</option>)}</select></Field>
      </div>
      <div className="upload-actions"><Button variant="secondary" onClick={clearForm}>Clear</Button><Button variant="secondary" disabled={!file} onClick={processImage}>Process image</Button><Button disabled={!file} onClick={saveCase}>Save local case</Button></div>
      <p className="upload-footnote">Local case metadata remains in this browser. No backend API is called.</p>
    </Card>
  </div>;
}
