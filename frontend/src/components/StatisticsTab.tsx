import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface StatisticsOverview {
  total_detections: number
  legitimate_detections: number
  false_positives: number
  high_confidence_count: number
  avg_confidence_score: number
  repositories_count: number
}

interface SecretTypeStats {
  secret_type: string
  count: number
  repositories_affected: number
  avg_confidence: number
}

interface RepositoryStats {
  repository_id: number
  repository_name: string
  total_secrets: number
  high_confidence_count: number
  types_breakdown: { [type: string]: number }
  last_scanned_at: string
  scan_status: string
}

interface TimelineEntry {
  date: string
  count: number
  by_type: { [type: string]: number }
}

interface ScanHistoryItem {
  id: number
  repository_name: string
  scan_date: string
  commits_scanned: number
  secrets_found: number
  execution_time_seconds: number
  status: string
}

interface ScanHistoryResponse {
  items: ScanHistoryItem[]
  total: number
  total_commits_scanned: number
  total_secrets_found: number
  total_scan_time_seconds: number
}

export const StatisticsTab: React.FC<{ repositories: any[]; apiUrl: string }> = ({ repositories, apiUrl }) => {
  const [overview, setOverview] = useState<StatisticsOverview | null>(null)
  const [byType, setByType] = useState<SecretTypeStats[]>([])
  const [byRepository, setByRepository] = useState<RepositoryStats[]>([])
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [scanHistory, setScanHistory] = useState<ScanHistoryItem[]>([])
  const [scanHistoryTotal, setScanHistoryTotal] = useState(0)
  const [scanHistoryAggregates, setScanHistoryAggregates] = useState<any>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 20
  
  const [selectedRepository, setSelectedRepository] = useState<number | null>(null)

  const [cacheTime, setCacheTime] = useState<number | null>(null)
  const cacheExpiry = 5 * 60 * 1000 // 5 minutes

  const fetchStatistics = async () => {
    try {
      setLoading(true)
      setError(null)

      const now = Date.now()
      if (cacheTime && now - cacheTime < cacheExpiry && overview) {
        setLoading(false)
        return
      }

      const [overviewRes, typeRes, repoRes, timelineRes, historyRes] = await Promise.allSettled([
        fetch(`${apiUrl}/stats/overview`),
        fetch(`${apiUrl}/stats/by-type`),
        fetch(`${apiUrl}/stats/by-repository`),
        fetch(`${apiUrl}/stats/timeline?days=30`),
        fetch(`${apiUrl}/stats/scan-history?limit=${itemsPerPage}&offset=0`),
      ])

      if (overviewRes.status === 'fulfilled' && overviewRes.value.ok) {
        const data = await overviewRes.value.json()
        setOverview(data)
      }

      if (typeRes.status === 'fulfilled' && typeRes.value.ok) {
        const data = await typeRes.value.json()
        setByType(Array.isArray(data) ? data : [])
      }

      if (repoRes.status === 'fulfilled' && repoRes.value.ok) {
        const data = await repoRes.value.json()
        setByRepository(Array.isArray(data) ? data : [])
      }

      if (timelineRes.status === 'fulfilled' && timelineRes.value.ok) {
        const data = await timelineRes.value.json()
        setTimeline(Array.isArray(data) ? data : [])
      }

      if (historyRes.status === 'fulfilled' && historyRes.value.ok) {
        const data: ScanHistoryResponse = await historyRes.value.json()
        setScanHistory(data.items || [])
        setScanHistoryTotal(data.total || 0)
        setScanHistoryAggregates({
          total_commits: data.total_commits_scanned || 0,
          total_secrets: data.total_secrets_found || 0,
          total_time: data.total_scan_time_seconds || 0,
        })
      }

      setCacheTime(now)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatistics()
  }, [])

  const handleRefresh = () => {
    setCacheTime(null)
    fetchStatistics()
  }

  const filteredByType = selectedRepository
    ? byType.filter(t => {
        const repo = byRepository.find(r => r.repository_id === selectedRepository)
        return repo && repo.types_breakdown[t.secret_type]
      })
    : byType

  const filteredByRepository = selectedRepository
    ? byRepository.filter(r => r.repository_id === selectedRepository)
    : byRepository

  const filteredScanHistory = selectedRepository
    ? scanHistory.filter(item => {
        const repo = repositories.find(r => r.name === item.repository_name && r.id === selectedRepository)
        return !!repo
      })
    : scanHistory

  const handleNextPage = () => {
    if ((currentPage * itemsPerPage) < scanHistoryTotal) {
      const newPage = currentPage + 1
      setCurrentPage(newPage)
      fetchScanHistory(newPage * itemsPerPage)
    }
  }

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      const newPage = currentPage - 1
      setCurrentPage(newPage)
      fetchScanHistory((newPage - 1) * itemsPerPage)
    }
  }

  const fetchScanHistory = async (offset: number) => {
    try {
      const response = await fetch(`${apiUrl}/stats/scan-history?limit=${itemsPerPage}&offset=${offset}`)
      if (response.ok) {
        const data: ScanHistoryResponse = await response.json()
        setScanHistory(data.items || [])
      }
    } catch (err) {
      console.error('Error fetching scan history:', err)
    }
  }

  if (error && !overview) {
    return (
      <section className="section">
        <div className="section-header">
          <h2>Statistics</h2>
          <button onClick={handleRefresh} className="btn btn-primary">Refresh</button>
        </div>
        <div className="error">Error: {error}</div>
      </section>
    )
  }

  const SkeletonCard = () => (
    <div className="skeleton-card">
      <div className="skeleton-line"></div>
    </div>
  )

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    return `${Math.round(seconds / 60)}m`
  }

  return (
    <section className="section">
      <div className="section-header">
        <h2>Statistics</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select
            value={selectedRepository || ''}
            onChange={(e) => {
              setSelectedRepository(e.target.value ? parseInt(e.target.value) : null)
              setCurrentPage(1)
            }}
            style={{
              padding: '0.5rem 0.75rem',
              border: '1px solid #e5e7eb',
              borderRadius: '0.375rem',
              fontSize: '0.9rem'
            }}
          >
            <option value="">All Repositories</option>
            {repositories.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name} ({repo.secrets_found} secrets)
              </option>
            ))}
          </select>
          <button onClick={handleRefresh} className="btn btn-primary">Refresh</button>
        </div>
      </div>

      <div className="stats-grid">
        {loading && !overview ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : overview ? (
          <>
            <div className="stat-card">
              <div className="stat-number">{overview.total_detections}</div>
              <div className="stat-label">Total Detections</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#10b981' }}>{overview.legitimate_detections}</div>
              <div className="stat-label">Legitimate Detections</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#f59e0b' }}>{overview.false_positives}</div>
              <div className="stat-label">False Positives</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#3b82f6' }}>{overview.high_confidence_count}</div>
              <div className="stat-label">High Confidence ({'>='} 0.8)</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#8b5cf6' }}>{overview.repositories_count}</div>
              <div className="stat-label">Repositories Scanned</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#ec4899' }}>{overview.avg_confidence_score.toFixed(2)}</div>
              <div className="stat-label">Avg Confidence Score</div>
            </div>
          </>
        ) : null}
      </div>

      <div className="statistics-main-grid">
        <div className="stat-section">
          <h3>Detections by Secret Type</h3>
          {loading && !byType.length ? <SkeletonCard /> : filteredByType.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={filteredByType}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="secret_type" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state">No data available</div>}
        </div>

        <div className="stat-section">
          <h3>Detections by Repository</h3>
          {loading && !byRepository.length ? <SkeletonCard /> : filteredByRepository.length > 0 ? (
            <div className="repository-stats-table">
              <table>
                <thead><tr><th>Repository</th><th>Secrets</th><th>High Conf</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredByRepository.map((repo) => (
                    <tr key={repo.repository_id}>
                      <td className="repo-name">{repo.repository_name}</td>
                      <td>{repo.total_secrets}</td>
                      <td>{repo.high_confidence_count}</td>
                      <td><span className={`status-badge ${repo.scan_status}`}>{repo.scan_status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="empty-state">No repositories scanned yet</div>}
        </div>
      </div>

      <div className="stat-section full-width">
        <h3>Detection Trends (Last 30 Days)</h3>
        {loading && !timeline.length ? <SkeletonCard /> : timeline.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" name="Total Detections" />
            </LineChart>
          </ResponsiveContainer>
        ) : <div className="empty-state">No timeline data available</div>}
      </div>

      <div className="stat-section full-width">
        <h3>Scan History</h3>
        {scanHistoryAggregates && (
          <div className="aggregates-summary">
            <div className="aggregate-item"><span className="aggregate-label">Total Commits Scanned:</span><span className="aggregate-value">{scanHistoryAggregates.total_commits}</span></div>
            <div className="aggregate-item"><span className="aggregate-label">Total Secrets Found:</span><span className="aggregate-value">{scanHistoryAggregates.total_secrets}</span></div>
            <div className="aggregate-item"><span className="aggregate-label">Total Scan Time:</span><span className="aggregate-value">{formatTime(scanHistoryAggregates.total_time)}</span></div>
          </div>
        )}

        {loading && !scanHistory.length ? <SkeletonCard /> : filteredScanHistory.length > 0 ? (
          <>
            <div className="scan-history-table">
              <table>
                <thead><tr><th>Repository</th><th>Scan Date</th><th>Commits</th><th>Secrets</th><th>Time</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredScanHistory.map((item) => (
                    <tr key={item.id}>
                      <td>{item.repository_name}</td>
                      <td>{new Date(item.scan_date).toLocaleDateString()}</td>
                      <td>{item.commits_scanned}</td>
                      <td>{item.secrets_found}</td>
                      <td>{formatTime(item.execution_time_seconds)}</td>
                      <td><span className={`status-badge ${item.status}`}>{item.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <button onClick={handlePreviousPage} disabled={currentPage === 1} className="btn btn-secondary">Previous</button>
              <span className="pagination-info">Page {currentPage} of {Math.ceil(scanHistoryTotal / itemsPerPage)} (Showing {(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, scanHistoryTotal)} of {scanHistoryTotal})</span>
              <button onClick={handleNextPage} disabled={currentPage * itemsPerPage >= scanHistoryTotal} className="btn btn-secondary">Next</button>
            </div>
          </>
        ) : <div className="empty-state">No scan history available</div>}
      </div>
    </section>
  )
}
