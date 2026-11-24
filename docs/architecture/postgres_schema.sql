-- ==============================================================================
-- StenoVision: PostgreSQL Primary Database DDL Schema
-- Reference: Artery Segmentation & Stenosis Detection Deep Learning Platform
-- ==============================================================================

-- 1. Users Table (RBAC Authentication & Personnel Directory)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(60) NOT NULL DEFAULT 'Data Scientist',
    department VARCHAR(100) NOT NULL DEFAULT 'Deep Learning Core',
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Cases Table (Coronary Angiogram Patient Studies)
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    case_code VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    patient_id_code VARCHAR(50),
    patient_name VARCHAR(120),
    age INTEGER,
    gender VARCHAR(20),
    patient_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cases_code ON cases(case_code);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_created_by ON cases(created_by_id);

-- 3. Case Images Table (Medical Image Storage Metadata)
CREATE TABLE IF NOT EXISTS case_images (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_key VARCHAR(500) NOT NULL UNIQUE,
    storage_tier VARCHAR(50) NOT NULL DEFAULT 'raw', -- raw, masks, xai, reports
    modality VARCHAR(50) NOT NULL DEFAULT 'XCA',      -- XCA, DICOM
    file_size INTEGER NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_case_images_case_id ON case_images(case_id);
CREATE INDEX IF NOT EXISTS idx_case_images_sha256 ON case_images(sha256);

-- 4. Analysis Findings Table (QCA Calipers, Grad-CAM & 5-Category Severity)
CREATE TABLE IF NOT EXISTS analysis_findings (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES case_images(id) ON DELETE CASCADE,
    lesion_id INTEGER NOT NULL DEFAULT 1,
    bbox_json VARCHAR(100) DEFAULT '[]',
    centroid_json VARCHAR(50) DEFAULT '[]',
    probability_stenosis DOUBLE PRECISION DEFAULT 0.0,
    mld_mm DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    rvd_mm DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    pct_stenosis DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    lesion_length_mm DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    coronary_branch VARCHAR(120) NOT NULL DEFAULT 'LAD',
    segment_code VARCHAR(50) NOT NULL DEFAULT 'LAD-Mid',
    
    -- 5 Standardized Severity Categories: Normal | Mild | Moderate | Severe | Critical
    severity_category VARCHAR(50) NOT NULL DEFAULT 'Normal',
    clinical_label VARCHAR(200) DEFAULT '',
    hemodynamic_significance VARCHAR(200) DEFAULT '',
    clinical_recommendation TEXT DEFAULT '',
    
    -- Medical Local Storage Paths
    xai_plot_key VARCHAR(500),
    mask_key VARCHAR(500),
    
    latency_ms DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_findings_image_id ON analysis_findings(image_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON analysis_findings(severity_category);
CREATE INDEX IF NOT EXISTS idx_findings_branch ON analysis_findings(coronary_branch);

-- 5. Seed Personnel Directory (Roles & Credentials)
INSERT INTO users (full_name, email, role, department, hashed_password, is_active)
VALUES
    ('Sathiya (Lead Dev)', 'sathiya@stenovision.ai', 'Developer', 'Lead AI & System Engineering', '$2b$12$e80yq91l0h2XoYj44o7D3OiV4n5jR2X1T3pG3C8c0B1a0q.K9mK/m', TRUE),
    ('Dr. Aris Thorne', 'a.thorne@stenovision.org', 'Radiologist / Clinician', 'Clinical Diagnostics', '$2b$12$e80yq91l0h2XoYj44o7D3OiV4n5jR2X1T3pG3C8c0B1a0q.K9mK/m', TRUE),
    ('Prof. David Chen', 'd.chen@stenovision.org', 'Medical Researcher', 'Cardiovascular Research', '$2b$12$e80yq91l0h2XoYj44o7D3OiV4n5jR2X1T3pG3C8c0B1a0q.K9mK/m', TRUE),
    ('Dr. Helena Rostova', 'h.rostova@stenovision.org', 'Data Scientist', 'Data Science', '$2b$12$e80yq91l0h2XoYj44o7D3OiV4n5jR2X1T3pG3C8c0B1a0q.K9mK/m', TRUE),
    ('Sophia Martinez', 's.martinez@stenovision.org', 'Administrator', 'Administration', '$2b$12$e80yq91l0h2XoYj44o7D3OiV4n5jR2X1T3pG3C8c0B1a0q.K9mK/m', TRUE)
ON CONFLICT (email) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    department = EXCLUDED.department;

