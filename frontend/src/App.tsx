import { useState, useEffect } from 'react'
import './App.css'
import { RepositoriesTab, Repository } from './components/RepositoriesTab'
import { DetectionsTab } from './components/DetectionsTab'
import { StatisticsTab } from './components/StatisticsTab'

function App() {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'repositories' | 'detections' | 'stats'>('repositories')

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

  useEffect(() => {
    fetchRepositories()
  }, [])

  const fetchRepositories = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/repos/`)
      if (!response.ok) {
        throw new Error('Failed to fetch repositories')
      }
      const data = await response.json()
      setRepositories(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const startScan = async (repoId: number) => {
    try {
      const response = await fetch(`${API_URL}/scan/repository/${repoId}`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error('Failed to start scan')
      }
      const data = await response.json()
      console.log('Scan started:', data)
      fetchRepositories() // Refresh repositories
    } catch (err) {
      console.error('Error starting scan:', err)
    }
  }

  const deleteRepository = async (repoId: number) => {
    if (!confirm('Are you sure you want to delete this repository?')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/repos/${repoId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('Failed to delete repository')
      }
      console.log('Repository deleted')
      fetchRepositories() // Refresh repositories
    } catch (err) {
      console.error('Error deleting repository:', err)
      alert('Error: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  const addRepositoryFromGitHub = async (repoName: string) => {
    // Extract owner/repo from URL or use as is
    const repoIdentifier = repoName.includes('github.com') 
      ? repoName.split('/').slice(-2).join('/')
      : repoName
    
    const response = await fetch(`${API_URL}/scan/repository-from-github?repo_name=${encodeURIComponent(repoIdentifier)}`, {
      method: 'POST'
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      // Parse error message from response
      const errorMsg = data.detail || 'Failed to add repository'
      throw new Error(errorMsg)
    }
    
    console.log('Repository added:', data)
    alert('✅ Repository added successfully!\n\nScanned ' + data.scan_result?.commits_scanned + ' commits, found ' + data.scan_result?.secrets_found + ' secrets')
    fetchRepositories() // Refresh repositories
  }

  const scanTrendingRepositories = async () => {
    const response = await fetch(`${API_URL}/scan/trending`, { method: 'POST' })
    const data = await response.json()
    alert('✅ ' + data.message)
    // Refresh repos after 5 seconds to show newly scanned repos
    setTimeout(fetchRepositories, 5000)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>🔐 GitHub Secret Scanner Bot</h1>
          <p>Detect and manage exposed secrets in GitHub repositories</p>
        </div>
      </header>

      <nav className="navbar">
        <button
          className={`nav-btn ${activeTab === 'repositories' ? 'active' : ''}`}
          onClick={() => setActiveTab('repositories')}
        >
          📦 Repositories
        </button>
        <button
          className={`nav-btn ${activeTab === 'detections' ? 'active' : ''}`}
          onClick={() => setActiveTab('detections')}
        >
          🚨 Detections
        </button>
        <button
          className={`nav-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          📊 Statistics
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'repositories' && (
          <RepositoriesTab
            repositories={repositories}
            loading={loading}
            error={error}
            onRefresh={fetchRepositories}
            onAddRepository={addRepositoryFromGitHub}
            onScanTrending={scanTrendingRepositories}
            onScanRepository={startScan}
            onDeleteRepository={deleteRepository}
            apiUrl={API_URL}
          />
        )}

        {activeTab === 'detections' && (
          <DetectionsTab
            repositories={repositories}
            apiUrl={API_URL}
          />
        )}

        {activeTab === 'stats' && (
          <StatisticsTab
            repositories={repositories}
            apiUrl={API_URL}
          />
        )}
      </main>

      <footer className="footer">
        <p>&copy; 2024 GitHub Secret Scanner Bot. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
