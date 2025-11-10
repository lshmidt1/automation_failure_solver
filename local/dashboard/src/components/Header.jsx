import React from 'react'

function Header({ lastUpdate, onRefresh, loading }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1>Jenkins Failure Analyzer</h1>
          <p className="subtitle">AI-Powered Root Cause Analysis</p>
        </div>
        
        <div className="header-right">
          {lastUpdate && (
            <span className="last-update">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          
          <button 
            className="refresh-btn"
            onClick={onRefresh}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header