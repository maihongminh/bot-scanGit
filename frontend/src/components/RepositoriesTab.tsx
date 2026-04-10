import { useState, useEffect } from 'react'

export interface Repository {
  id: number
  name: string
  url: string
  scan_status: 'scanning' | 'completed'
  secrets_found: number
  last_scanned_at?: string
}

export function RepositoriesTab({
  repositories,
  loading,
  error,
  onRefresh,
  onAddRepository,
  onScanTrending,
  onScanRepository,
  onDeleteRepository,
  apiUrl,
}: {
  repositories: Repository[]
  loading: boolean
  error: string | null
  onRefresh: () => void
  onAddRepository: (repoName: string) => Promise<void>
  onScanTrending: () => Promise<void>
  onScanRepository: (repoId: number) => Promise<void>
  onDeleteRepository: (repoId: number) => Promise<void>
  apiUrl: string
}) {
  const [repoName, setRepoName] = useState('')
  const [adding, setAdding] = useState(false)
  const [scanningTrending, setScanningTrending] = useState(false)

  const handleAddRepository = async () => {
    if (!repoName.trim()) {
      alert('Please enter a repository name (e.g., python/cpython)')
      return
    }

    try {
      setAdding(true)
      await onAddRepository(repoName)
      setRepoName('')
    } finally {
      setAdding(false)
    }
  }

  const handleScanTrending = async () => {
    try {
      setScanningTrending(true)
      await onScanTrending()
    } finally {
      setScanningTrending(false)
    }
  }

  return (
    <section className="section">
      <div className="section-header">
        <h2>📦 Repositories</h2>
        <button onClick={onRefresh} className="btn btn-primary">
          🔄 Refresh
        </button>
      </div>

      <div className="add-repo-form">
        <div className="form-section">
          <h3>Add Repository from GitHub</h3>
          <div className="form-group">
            <input
              type="text"
              placeholder="e.g., python/cpython"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              className="form-input"
            />
            <button
              onClick={handleAddRepository}
              disabled={adding}
              className="btn btn-secondary"
            >
              {adding ? '⏳ Adding...' : '➕ Add Repository'}
            </button>
          </div>
        </div>

        <div className="form-section">
          <h3>Scan Trending Repositories</h3>
          <p className="form-description">
            Automatically scan the most popular repositories on GitHub
          </p>
          <button
            onClick={handleScanTrending}
            disabled={scanningTrending}
            className="btn btn-primary"
          >
            {scanningTrending ? '⏳ Scanning trending repositories...' : '🔥 Scan Trending Repos'}
          </button>
        </div>
      </div>

      {loading && <div className="loading">Loading repositories...</div>}
      {error && <div className="error">Error: {error}</div>}

      {!loading && repositories.length === 0 && (
        <div className="empty-state">
          <p>No repositories found</p>
        </div>
      )}

      {!loading && repositories.length > 0 && (
        <div className="repositories-grid">
          {repositories.map((repo) => (
            <div key={repo.id} className="repo-card">
              <div className="repo-header">
                <a href={repo.url} target="_blank" rel="noopener noreferrer">
                  <h3>{repo.name}</h3>
                </a>
                <span className={`status-badge ${repo.scan_status}`}>
                  {repo.scan_status}
                </span>
              </div>

              <div className="repo-stats">
                <div className="stat">
                  <span className="stat-label">Secrets Found:</span>
                  <span className="stat-value">{repo.secrets_found}</span>
                </div>
                {repo.last_scanned_at && (
                  <div className="stat">
                    <span className="stat-label">Last Scanned:</span>
                    <span className="stat-value">
                      {new Date(repo.last_scanned_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              <div className="repo-actions">
                <button
                  onClick={() => onScanRepository(repo.id)}
                  disabled={repo.scan_status === 'scanning'}
                  className="btn btn-secondary"
                >
                  {repo.scan_status === 'scanning' ? '⏳ Scanning...' : '🔍 Scan'}
                </button>
                <button
                  onClick={() => onDeleteRepository(repo.id)}
                  className="btn btn-danger"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
