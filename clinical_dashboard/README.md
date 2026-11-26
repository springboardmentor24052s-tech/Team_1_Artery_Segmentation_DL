# Clinical Dashboard & Workstation Architecture
## Technical Report & Source Code Workspace

**Internship Program:** Infosys Springboard Virtual Internship 7.0  
**Milestone:** Milestone 4 (Weeks 7 & 8)  
**Author:** Sathiyamoorthi K  
**Role:** Lead System Architect & Backend Integration  
**Focus:** Full-Stack Clinical Workstation Layout, Responsive Next.js 15 Dashboard, Enterprise Role-Based Access Control (RBAC), and HIPAA Audit Logging Interface  

---

### 1. The Challenge We Addressed

In catheterization laboratories and clinical cardiology suites, diagnostic AI models are ineffective if isolated behind command-line scripts or disconnected notebooks. Interventional cardiologists and clinical fellows require an integrated, high-throughput web workstation that delivers:
- **Instant Triage at a Glance:** Immediate visibility into pending angiograms, critical stenosis alerts ($>70\%$ diameter stenosis), and departmental case volume.
- **Role-Based Access Control (RBAC):** Strict clinical permission enforcement ensuring that only authorized personnel can approve reports, modify case records, or inspect system audit logs.
- **Audit Logging & Regulatory Compliance:** Comprehensive, tamper-evident tracking of user logins, role switches, and administrative actions.
- **Responsive Clinical Design:** A low-cognitive-load user interface adhering to accessibility standards and high-contrast clinical displays.

---

### 2. Architecture & Implementation

#### A. Next.js 15 Clinical Workstation Architecture (`code/app/`, `code/components/`)
We engineered a modular React 19 / Next.js 15 workstation featuring:
1. **Shell & Navigation Layout (`components/MainLayout.tsx`, `components/Sidebar.tsx`, `components/Header.tsx`):**
   - Collapsible high-density navigation sidebar with role-aware route visibility.
   - Clinical header featuring active clinician badge, institutional profile, and quick case search.
2. **Clinical Dashboard (`components/screens/DashboardScreen.tsx`):**
   - KPI summary metric cards (`SummaryCard.tsx`) tracking total processed cases, detected lesions, critical stenosis alerts, and mean inference latency.
   - Real-time case queue data table (`DataTable.tsx`) with status indicators (`StatusIndicator.tsx`) and dynamic filtering (`FilterControls.tsx`).
3. **Public Landing Experience (`components/screens/LandingPage.tsx`):**
   - Clean, professional entry point highlighting core diagnostic capabilities, multi-modality DICOM support, and deep learning pipeline architecture.

#### B. Enterprise Role-Based Access Control (`code/lib/permissions.ts`, `code/hooks/useAuth.ts`)
We implemented a strict hierarchical RBAC system defining granular permissions across five clinical personas:
- **Admin:** User management, audit logs, model registry configuration, system health monitoring.
- **Cardiologist:** Full diagnostic analysis, manual QCA caliper adjustments, report approval, and export.
- **Radiologist:** Image upload, preprocessing review, segmentation inspection, preliminary reporting.
- **Fellow:** Case review, educational XAI visualization, candidate lesion inspection (read-only approval).
- **Reviewer:** External quality assurance review and validation feedback.

#### C. User Management & Audit Logging (`components/screens/UserManagementScreen.tsx`)
We developed an administrative audit dashboard:
- Full chronological log of user sign-ins, IP addresses, browser user-agents, and authentication timestamps.
- Tabular search and filtering across clinical departments and active/inactive credential statuses.

---

### 3. Directory Structure

```text
clinical_dashboard/
├── code/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── screens/
│   │   │   ├── DashboardScreen.tsx
│   │   │   ├── LandingPage.tsx
│   │   │   └── UserManagementScreen.tsx
│   │   ├── DataTable.tsx
│   │   ├── FilterControls.tsx
│   │   ├── FormInput.tsx
│   │   ├── Header.tsx
│   │   ├── MainLayout.tsx
│   │   ├── SearchField.tsx
│   │   ├── Sidebar.tsx
│   │   ├── StatusIndicator.tsx
│   │   ├── SummaryCard.tsx
│   │   └── UserAvatar.tsx
│   ├── hooks/
│   │   └── useAuth.ts
│   └── lib/
│       └── permissions.ts
├── results/
│   ├── admin_audit_management.png
│   ├── landing_page_desktop.png
│   ├── medical_image_upload.png
│   └── reports/
│       ├── StenoVision_Milestone_4_Report.docx
│       ├── StenoVision_Milestone_4_Report.md
│       ├── StenoVision_Project_Documentation.docx
│       └── StenoVision_Project_Documentation.md
└── README.md
```

---

### 4. Verification & Testing

The workstation interface and dashboard components were validated with comprehensive automated test suites:
- **Component Unit Tests:** Verified RBAC permission evaluation (`hasPermission()`), route protection, and navigation state.
- **Responsive Layout:** Tested across $1920 \times 1080$, $1440 \times 900$, and tablet viewports.
- **Cross-Service Integration:** Seamless end-to-end communication with the FastAPI backend `/api/v1/cases`, `/api/v1/reports`, and `/api/v1/users` endpoints.
