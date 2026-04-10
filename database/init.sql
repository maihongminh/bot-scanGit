-- Create database
CREATE DATABASE github_scanner;

-- Connect to database
\c github_scanner;

-- Repositories table
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(500) NOT NULL,
    description TEXT,
    owner VARCHAR(255),
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    language VARCHAR(50),
    is_public BOOLEAN DEFAULT TRUE,
    last_scanned_at TIMESTAMP,
    next_scan_at TIMESTAMP,
    scan_status VARCHAR(50) DEFAULT 'pending', -- pending, scanning, completed, error
    total_commits INTEGER DEFAULT 0,
    secrets_found INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Commits table
CREATE TABLE commits (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    commit_hash VARCHAR(40) NOT NULL,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    message TEXT,
    commit_url VARCHAR(500),
    scanned_at TIMESTAMP,
    has_secrets BOOLEAN DEFAULT FALSE,
    scan_status VARCHAR(50) DEFAULT 'pending', -- pending, scanning, completed, error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, commit_hash)
);

-- Detections table
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    commit_id INTEGER NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    secret_type VARCHAR(100) NOT NULL, -- aws_key, google_api, openai_key, claude_key, etc
    secret_pattern VARCHAR(50), -- The matched pattern name
    matched_value VARCHAR(255), -- First 100 chars of matched secret (masked)
    line_number INTEGER,
    confidence_score FLOAT DEFAULT 0.0, -- 0.0 to 1.0
    is_false_positive BOOLEAN DEFAULT FALSE,
    remediation_status VARCHAR(50) DEFAULT 'pending', -- pending, notified, fixed, dismissed
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan history table
CREATE TABLE scan_history (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) DEFAULT 'full', -- full, incremental, manual
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_commits_scanned INTEGER DEFAULT 0,
    total_secrets_found INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_message TEXT,
    scan_status VARCHAR(50) DEFAULT 'running', -- running, completed, error
    execution_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detection statistics table
CREATE TABLE detection_statistics (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    secret_type VARCHAR(100),
    count INTEGER DEFAULT 0,
    repositories_affected INTEGER DEFAULT 0,
    avg_confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-specified repositories table
CREATE TABLE user_repositories (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_added_by VARCHAR(255),
    is_monitored BOOLEAN DEFAULT TRUE,
    monitor_frequency VARCHAR(50) DEFAULT 'hourly', -- hourly, daily, weekly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- False positives management table
CREATE TABLE false_positives (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    reason_code VARCHAR(100),
    reason_description TEXT,
    marked_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_repositories_status ON repositories(scan_status);
CREATE INDEX idx_repositories_last_scanned ON repositories(last_scanned_at);
CREATE INDEX idx_commits_repository ON commits(repository_id);
CREATE INDEX idx_commits_hash ON commits(commit_hash);
CREATE INDEX idx_detections_repository ON detections(repository_id);
CREATE INDEX idx_detections_commit ON detections(commit_id);
CREATE INDEX idx_detections_type ON detections(secret_type);
CREATE INDEX idx_detections_confidence ON detections(confidence_score);
CREATE INDEX idx_scan_history_repository ON scan_history(repository_id);
CREATE INDEX idx_detection_stats_date ON detection_statistics(date);
CREATE INDEX idx_false_positives_detection ON false_positives(detection_id);

-- Create views for dashboard
CREATE VIEW dashboard_summary AS
SELECT
    (SELECT COUNT(*) FROM repositories) as total_repositories,
    (SELECT COUNT(*) FROM repositories WHERE scan_status = 'scanning') as scanning_now,
    (SELECT COUNT(DISTINCT repository_id) FROM detections WHERE is_false_positive = FALSE) as repos_with_secrets,
    (SELECT COUNT(*) FROM detections WHERE is_false_positive = FALSE) as total_secrets_found,
    NOW() as last_updated;

CREATE VIEW recent_detections AS
SELECT
    d.id,
    d.file_path,
    d.secret_type,
    d.confidence_score,
    c.commit_hash,
    c.author_name,
    r.name as repository_name,
    d.detected_at
FROM detections d
JOIN commits c ON d.commit_id = c.id
JOIN repositories r ON d.repository_id = r.id
WHERE d.is_false_positive = FALSE
ORDER BY d.detected_at DESC
LIMIT 100;

CREATE VIEW secret_type_distribution AS
SELECT
    secret_type,
    COUNT(*) as count,
    COUNT(DISTINCT repository_id) as repositories_affected,
    AVG(confidence_score) as avg_confidence
FROM detections
WHERE is_false_positive = FALSE
GROUP BY secret_type
ORDER BY count DESC;

-- Grants (adjust user as needed)
GRANT ALL PRIVILEGES ON DATABASE github_scanner TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
