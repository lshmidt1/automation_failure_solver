import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Header from './components/Header'
import FailureList from './components/FailureList'
import FailureDetail from './components/FailureDetail'
import Stats from './components/Stats'
import './styles/App.css'

function App() {
  const [failures, setFailures] = useState([])
  const [selectedFailure, setSelectedFailure] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  // Fetch failures from API
  const fetchFailures = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/results')
      setFailures(response.data.results || [])
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      console.error('Error fetching failures:', err)
      setError('Failed to fetch data. Make sure the backend is running on port 5000.')
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchFailures()
  }, [])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchFailures, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <Header 
        lastUpdate={lastUpdate} 
        onRefresh={fetchFailures}
        loading={loading}
      />
      
      <div className="container">
        <Stats failures={failures} />
        
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}
        
        <div className="content">
          <div className="failures-panel">
            <FailureList 
              failures={failures}
              selectedFailure={selectedFailure}
              onSelect={setSelectedFailure}
              loading={loading}
            />
          </div>
          
          {selectedFailure && (
            <div className="detail-panel">
              <FailureDetail 
                failure={selectedFailure}
                onClose={() => setSelectedFailure(null)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App