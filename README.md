# StenoVision

React frontend for the StenoVision medical imaging research prototype, styled with regular CSS.

## Run the frontend

```powershell
npm install
npm run dev
```

To create a production build:

```powershell
npm run build
```

## Screens

The app currently includes five screens: Login, Dashboard, Image Upload, Analysis Results, and User Management. Other screens have been removed for now.

Image Upload supports image selection, validation, preview, browser-side preprocessing, and saving case metadata in browser local storage. Uploaded image files and previews are not retained after leaving the Upload page. Analysis Results is a placeholder until model inference is connected. Login and User Management are UI demonstrations; there is no authentication or backend connection.

Supported browser images: PNG, JPG/JPEG, WEBP, BMP. Maximum 15 MB. DICOM/NIfTI are not supported. This prototype is not a medical diagnostic tool; use public or de-identified research data and follow dataset terms.
