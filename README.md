# StenoVision

StenoVision is a responsive React frontend for an artery-imaging research prototype. It runs in the browser and does not require a backend.

## Run the frontend

```powershell
npm install
npm run dev
```

Create a production build with `npm run build`. Vite writes generated output to `dist/`; use `npm run preview` to serve that build locally. The generated `dist/` directory is not required for development and can be recreated at any time.

## Pages and features

- **Login:** demo-only form; valid email and a password with at least four characters opens the workspace. No credentials are authenticated or stored.
- **Dashboard:** case counts, recent cases, and shortcuts to case management and upload.
- **Case Management:** search and filter cases, open case details, and remove browser-local case metadata. Sample cases are read-only.
- **Image Upload:** accepts PNG, JPG/JPEG, WEBP, and BMP images up to 15 MB; includes validation, previews, browser-side grayscale conversion, intensity normalization, and resizing. Case metadata is saved to browser local storage. Image files and previews are not retained after leaving the page.
- **Analysis Configuration:** save browser-local preprocessing preferences per case. Settings do not run model inference.
- **Analysis Results:** shows case metadata; segmentation results and metrics are unavailable because no model or backend is connected.
- **Case Details:** displays metadata and research notes for the selected case.
- **Reports:** summarizes case metadata and downloads a CSV export. The export does not contain image files or model results.
- **User Management:** manage demo users in browser local storage. This does not create real accounts.

The app makes no backend requests. DICOM/NIfTI files are not supported. There is no Python preprocessing directory or script in this project.

Use public or de-identified research data, follow dataset terms, and do not enter patient-identifying information. This prototype is not a medical diagnostic tool.
