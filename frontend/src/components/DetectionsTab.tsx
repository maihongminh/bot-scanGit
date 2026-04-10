import { useState, useEffect } from 'react'

interface Detection {
  id: number
  repository_id: number
  commit_id: number
  file_path: string
  secret_type: string
  secret_pattern?: string
  matched_value?: string
  line_number?: number
  confidence_score: number
  is_false_positive: boolean
  remediation_status: string
  detected_at: string
  created_at: string
  updated_at: string
}

interface Repository {
  id: number
  name: string
  url: string
}

interface DetectionFilters {
  repositoryId?: number
  secretType?: string
  minConfidence: number
  excludeFalsePositives: boolean
  searchPath: string
  page: number
  pageSize: number
}

interface DetectionStats {
  total: number
  high_confidence: number
  false_positives: number
  by_type: { [key: string]: number }
}

const SECRET_TYPES = [
  'AWS_KEY',
  'GOOGLE_API_KEY',
  'OPENAI_KEY',
  'CLAUDE_KEY',
  'GITHUB_TOKEN',
  'SLACK_TOKEN',
  'SSH_PRIVATE_KEY',
  'DATABASE_CREDENTIALS',
  'HIGH_ENTROPY_STRING',
]

const SECRET_TYPE_ICONS: { [key: string]: string } = {
  'AWS_KEY': '🔑',
  'GOOGLE_API_KEY': '🔍',
  'OPENAI_KEY': '🤖',
  'CLAUDE_KEY': '🧠',
  'GITHUB_TOKEN': '🐙',
  'SLACK_TOKEN': '💬',
  'SSH_PRIVATE_KEY': '🔐',
  'DATABASE_CREDENTIALS': '🗄️',
  'HIGH_ENTROPY_STRING': '⚠️',
}

export function DetectionsTab({
  repositories,
  apiUrl,
}: {
  repositories: Repository[]
  apiUrl: string
}) {
  const [detections, setDetections] = useState<Detection[]>([])
  const [stats, setStats] = useState<DetectionStats>({
    total: 0,
    high_confidence: 0,
    false_positives: 0,
    by_type: {},
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [markingFalsePositive, setMarkingFalsePositive] = useState(false)

  const [filters, setFilters] = useState<DetectionFilters>({
    repositoryId: undefined,
    secretType: undefined,
    minConfidence: 0,
    excludeFalsePositives: false,
    searchPath: '',
    page: 1,
    pageSize: 20,
  })

  // Fetch detections
  const fetchDetections = async () => {
    try {
      setLoading(true)
      setError(null)

      const queryParams = new URLSearchParams()
      if (filters.repositoryId) {
        queryParams.append('repository_id', filters.repositoryId.toString())
      }
      if (filters.secretType) {
        queryParams.append('secret_type', filters.secretType)
      }
      if (filters.minConfidence > 0) {
        queryParams.append('min_confidence', filters.minConfidence.toString())
      }
      if (filters.excludeFalsePositives) {
        queryParams.append('exclude_false_positives', 'true')
      }
      queryParams.append('page', filters.page.toString())
      queryParams.append('limit', filters.pageSize.toString())

      const response = await fetch(
        `${apiUrl}/detections/?${queryParams.toString()}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch detections')
      }

      const data = await response.json()
      setDetections(Array.isArray(data) ? data : data.items || [])

      // Calculate stats
      calculateStats(Array.isArray(data) ? data : data.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setDetections([])
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (detectionList: Detection[]) => {
    const total = detectionList.length
    const high_confidence = detectionList.filter((d) => d.confidence_score >= 0.8).length
    const false_positives = detectionList.filter((d) => d.is_false_positive).length

    const by_type: { [key: string]: number } = {}
    detectionList.forEach((d) => {
      by_type[d.secret_type] = (by_type[d.secret_type] || 0) + 1
    })

    setStats({
      total,
      high_confidence,
      false_positives,
      by_type,
    })
  }

  // Mark as false positive
  const markAsFalsePositive = async () => {
    if (!selectedDetection) return

    try {
      setMarkingFalsePositive(true)

      const response = await fetch(
        `${apiUrl}/detections/${selectedDetection.id}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            is_false_positive: !selectedDetection.is_false_positive,
          }),
        }
      )

      if (!response.ok) {
        throw new Error('Failed to update detection')
      }

      const updatedDetection = await response.json()
      setSelectedDetection(updatedDetection)

      // Refresh detections list
      fetchDetections()
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Unknown error'))
    } finally {
      setMarkingFalsePositive(false)
    }
  }

  // Load detections on mount and filter changes
  useEffect(() => {
    fetchDetections()
  }, [filters])

  const getRepositoryName = (repoId: number) => {
    const repo = repositories.find((r) => r.id === repoId)
    return repo?.name || `Repo #${repoId}`
  }

  const getConfidenceColor = (score: number): string => {
    if (score >= 0.8) return '#10b981' // green
    if (score >= 0.6) return '#f59e0b' // amber
    return '#ef4444' // red
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <section className="section">
      <div className="section-header">
        <h2>🚨 Detections</h2>
        <button onClick={() => fetchDetections()} className="btn btn-primary">
          🔄 Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {!loading && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats.total}</div>
            <div className="stat-label">Total Detections</div>
          </div>
          <div className="stat-card">
            <div className="stat-number" style={{ color: '#10b981' }}>
              {stats.high_confidence}
            </div>
            <div className="stat-label">High Confidence (≥0.8)</div>
          </div>
          <div className="stat-card">
            <div className="stat-number" style={{ color: '#f59e0b' }}>
              {stats.false_positives}
            </div>
            <div className="stat-label">False Positives</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">By Type</div>
            <div className="type-breakdown">
              {Object.entries(stats.by_type).map(([type, count]) => (
                <span key={type} className="type-badge">
                  {SECRET_TYPE_ICONS[type] || '🔍'} {type}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="detections-container">
        {/* Filters Sidebar */}
        <aside className="filters-sidebar">
          <h3>Filters</h3>

          <div className="filter-group">
            <label>Repository</label>
            <select
              value={filters.repositoryId || ''}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  repositoryId: e.target.value ? parseInt(e.target.value) : undefined,
                  page: 1,
                })
              }
            >
              <option value="">All Repositories</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Secret Type</label>
            <select
              value={filters.secretType || ''}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  secretType: e.target.value || undefined,
                  page: 1,
                })
              }
            >
              <option value="">All Types</option>
              {SECRET_TYPES.map((type) => (
                <option key={type} value={type}>
                  {SECRET_TYPE_ICONS[type]} {type}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>
              Min Confidence: {filters.minConfidence.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.minConfidence}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  minConfidence: parseFloat(e.target.value),
                  page: 1,
                })
              }
              className="slider"
            />
          </div>

          <div className="filter-group">
            <label>
              <input
                type="checkbox"
                checked={filters.excludeFalsePositives}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    excludeFalsePositives: e.target.checked,
                    page: 1,
                  })
                }
              />
              Hide False Positives
            </label>
          </div>

          <div className="filter-group">
            <label>Search File Path</label>
            <input
              type="text"
              placeholder="e.g., .env, config.py"
              value={filters.searchPath}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  searchPath: e.target.value,
                  page: 1,
                })
              }
              className="form-input"
            />
          </div>

          <button
            onClick={() =>
              setFilters({
                repositoryId: undefined,
                secretType: undefined,
                minConfidence: 0,
                excludeFalsePositives: false,
                searchPath: '',
                page: 1,
                pageSize: 20,
              })
            }
            className="btn btn-secondary"
          >
            Reset Filters
          </button>
        </aside>

        {/* Main Content */}
        <div className="detections-main">
          {loading && <div className="loading">Loading detections...</div>}
          {error && <div className="error">Error: {error}</div>}

          {!loading && detections.length === 0 && (
            <div className="empty-state">
              <p>No detections found</p>
            </div>
          )}

          {!loading && detections.length > 0 && (
            <div className="detections-list">
              {detections.map((detection) => (
                <div
                  key={detection.id}
                  className={`detection-card ${
                    detection.is_false_positive ? 'false-positive' : ''
                  }`}
                >
                  <div className="detection-header">
                    <div className="detection-type">
                      <span className="type-icon">
                        {SECRET_TYPE_ICONS[detection.secret_type] || '🔍'}
                      </span>
                      <span className="type-name">{detection.secret_type}</span>
                    </div>
                    <div className="detection-confidence">
                      <span
                        className="confidence-score"
                        style={{
                          background: getConfidenceColor(detection.confidence_score),
                        }}
                      >
                        {(detection.confidence_score * 100).toFixed(0)}%
                      </span>
                      {detection.is_false_positive && (
                        <span className="badge badge-warning">False Positive</span>
                      )}
                    </div>
                  </div>

                  <div className="detection-details">
                    <div className="detail-row">
                      <span className="label">File:</span>
                      <span className="value">{detection.file_path}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Repository:</span>
                      <span className="value">
                        {getRepositoryName(detection.repository_id)}
                      </span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Detected:</span>
                      <span className="value">{formatDate(detection.detected_at)}</span>
                    </div>
                  </div>

                  <div className="detection-actions">
                    <button
                      onClick={() => {
                        setSelectedDetection(detection)
                        setShowDetailModal(true)
                      }}
                      className="btn btn-secondary btn-small"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedDetection && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {SECRET_TYPE_ICONS[selectedDetection.secret_type]} Detection Details
              </h3>
              <button
                onClick={() => setShowDetailModal(false)}
                className="btn-close"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-section">
                <h4>Secret Information</h4>
                <div className="detail-item">
                  <span className="label">Type:</span>
                  <span className="value">{selectedDetection.secret_type}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Confidence:</span>
                  <span
                    className="value"
                    style={{
                      color: getConfidenceColor(selectedDetection.confidence_score),
                      fontWeight: 'bold',
                    }}
                  >
                    {(selectedDetection.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="label">Pattern:</span>
                  <span className="value">{selectedDetection.secret_pattern || 'N/A'}</span>
                </div>
              </div>

              <div className="detail-section">
                <h4>Location</h4>
                <div className="detail-item">
                  <span className="label">File:</span>
                  <span className="value">{selectedDetection.file_path}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Line:</span>
                  <span className="value">
                    {selectedDetection.line_number || 'Unknown'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="label">Repository:</span>
                  <span className="value">
                    {getRepositoryName(selectedDetection.repository_id)}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="label">Commit:</span>
                  <span className="value monospace">
                    #{selectedDetection.commit_id}
                  </span>
                </div>
              </div>

              <div className="detail-section">
                <h4>Timeline</h4>
                <div className="detail-item">
                  <span className="label">Detected At:</span>
                  <span className="value">
                    {new Date(selectedDetection.detected_at).toLocaleString()}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="label">Status:</span>
                  <span className="value">
                    {selectedDetection.is_false_positive ? (
                      <span style={{ color: '#f59e0b' }}>🚫 False Positive</span>
                    ) : (
                      <span style={{ color: '#10b981' }}>✓ Legitimate</span>
                    )}
                  </span>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                onClick={markAsFalsePositive}
                disabled={markingFalsePositive}
                className={`btn ${
                  selectedDetection.is_false_positive
                    ? 'btn-secondary'
                    : 'btn-warning'
                }`}
              >
                {markingFalsePositive
                  ? '⏳ Updating...'
                  : selectedDetection.is_false_positive
                  ? '✓ Remove False Positive Mark'
                  : '🚫 Mark as False Positive'}
              </button>
              <button
                onClick={() => setShowDetailModal(false)}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
