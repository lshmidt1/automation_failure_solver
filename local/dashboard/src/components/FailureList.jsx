import React from 'react'

function FailureList({ failures, selectedFailure, onSelect, loading }) {
  if (loading && failures.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading failures...</p>
      </div>
    )
  }

  if (failures.length === 0) {
    return (
      <div className="empty-state">
        <h3>🎉 No failures yet!</h3>
        <p>Trigger a Jenkins build failure to see analysis here.</p>
      </div>
    )
  }

  return (
    <div className="failure-list">
      <h2>Recent Failures ({failures.length})</h2>
      
      <div className="list">
        {failures.map((failure, index) => (
          <div
            key={index}
            className={`failure-item ${selectedFailure === failure ? 'selected' : ''} confidence-${failure.confidence}`}
            onClick={() => onSelect(failure)}
          >
            <div className="failure-header">
              <span className="job-name">{failure.job_name}</span>
              <span className="build-number">#{failure.build_number}</span>
            </div>
            
            <div className="failure-meta">
              <span className="timestamp">
                {new Date(failure.timestamp).toLocaleString()}
              </span>
              <span className={`confidence-badge ${failure.confidence}`}>
                {failure.confidence?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            
            <div className="root-cause-preview">
              {failure.root_cause?.substring(0, 100)}...
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FailureList