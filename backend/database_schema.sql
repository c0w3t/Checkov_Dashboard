-- PostgreSQL schema for Checkov Dashboard

-- ENUM types
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'severitylevel') THEN
        CREATE TYPE severitylevel AS ENUM ('critical','high','medium','low','info');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vulnerabilitystatus') THEN
        CREATE TYPE vulnerabilitystatus AS ENUM ('open','in_progress','resolved','ignored');
    END IF;
END$$;

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    repository_url VARCHAR(500),
    description TEXT,
    framework VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Scans
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL,
    commit_sha VARCHAR(255),
    branch VARCHAR(255),
    triggered_by VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    total_checks INTEGER DEFAULT 0,
    passed_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    skipped_checks INTEGER DEFAULT 0,
    scan_duration INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_metadata JSONB,
    error_message TEXT
);

-- Vulnerabilities
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    check_id VARCHAR(100) NOT NULL,
    check_name VARCHAR(500) NOT NULL,
    severity severitylevel NOT NULL,
    status vulnerabilitystatus DEFAULT 'open',
    resource_type VARCHAR(100),
    resource_name VARCHAR(255),
    file_path VARCHAR(1000) NOT NULL,
    line_number INTEGER,
    line_start INTEGER,
    line_end INTEGER,
    description TEXT,
    remediation TEXT,
    guideline_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_scan_id INTEGER REFERENCES scans(id),
    vulnerability_hash VARCHAR(64)
);

-- Policy configurations
CREATE TABLE IF NOT EXISTS policy_configs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    policy_type VARCHAR(50) NOT NULL,
    check_id VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    severity_override VARCHAR(50),
    custom_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    format VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    generated_by VARCHAR(255),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policies
CREATE TABLE IF NOT EXISTS policies (
    id SERIAL PRIMARY KEY,
    check_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    guideline TEXT,
    guideline_url VARCHAR(500),
    built_in BOOLEAN DEFAULT true,
    file_path VARCHAR(1000),
    code TEXT,
    supported_resources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File versions
CREATE TABLE IF NOT EXISTS file_versions (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(100) NOT NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    version_number INTEGER NOT NULL,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    change_summary VARCHAR(500),
    edited_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification settings & history
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    critical_recipients JSONB DEFAULT '[]',
    summary_recipients JSONB DEFAULT '[]',
    weekly_recipients JSONB DEFAULT '[]',
    critical_immediate_enabled BOOLEAN DEFAULT true,
    scan_summary_enabled BOOLEAN DEFAULT true,
    weekly_summary_enabled BOOLEAN DEFAULT true,
    scan_failed_enabled BOOLEAN DEFAULT true,
    critical_threshold INTEGER DEFAULT 1,
    high_threshold INTEGER DEFAULT 5,
    fixed_threshold INTEGER DEFAULT 1,
    summary_send_when VARCHAR(50) DEFAULT 'has_changes',
    summary_include_fixed BOOLEAN DEFAULT true,
    summary_include_new BOOLEAN DEFAULT true,
    summary_include_still_open BOOLEAN DEFAULT true,
    weekly_day VARCHAR(20) DEFAULT 'monday',
    weekly_time VARCHAR(10) DEFAULT '09:00',
    weekly_include_trends BOOLEAN DEFAULT true,
    digest_mode BOOLEAN DEFAULT false,
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start VARCHAR(10) DEFAULT '22:00',
    quiet_hours_end VARCHAR(10) DEFAULT '08:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_history (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    scan_id INTEGER REFERENCES scans(id) ON DELETE SET NULL,
    notification_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    recipients JSONB DEFAULT '[]',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'sent',
    error_message VARCHAR(1000),
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    fixed_count INTEGER DEFAULT 0,
    new_count INTEGER DEFAULT 0
);

-- API tokens
CREATE TABLE IF NOT EXISTS api_tokens (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT true,
    permissions TEXT,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scans_project ON scans(project_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at);

CREATE INDEX IF NOT EXISTS idx_vulnerabilities_scan ON vulnerabilities(scan_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_status ON vulnerabilities(status);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_check_id ON vulnerabilities(check_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_resolution_scan_id ON vulnerabilities(resolution_scan_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_hash ON vulnerabilities(vulnerability_hash);

CREATE INDEX IF NOT EXISTS idx_policy_configs_project ON policy_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_policy_configs_check_id ON policy_configs(check_id);

CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id);

CREATE INDEX IF NOT EXISTS idx_policies_check_id ON policies(check_id);
CREATE INDEX IF NOT EXISTS idx_policies_platform ON policies(platform);
CREATE INDEX IF NOT EXISTS idx_policies_severity ON policies(severity);
CREATE INDEX IF NOT EXISTS idx_policies_builtin ON policies(built_in);
CREATE INDEX IF NOT EXISTS idx_policies_category ON policies(category);
CREATE INDEX IF NOT EXISTS idx_policies_platform_severity ON policies(platform, severity);
CREATE INDEX IF NOT EXISTS idx_policies_builtin_platform ON policies(built_in, platform);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policy_configs_updated_at BEFORE UPDATE ON policy_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Backfill vulnerability_hash for existing rows (idempotent)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vulnerabilities' AND column_name = 'vulnerability_hash'
    ) THEN
        UPDATE vulnerabilities
        SET vulnerability_hash = MD5(
            COALESCE(check_id, '') || '|' || COALESCE(file_path, '') || '|' || COALESCE(CAST(line_number AS TEXT), '') || '|' || COALESCE(resource_name, '')
        )
        WHERE vulnerability_hash IS NULL;
    END IF;
END$$;

