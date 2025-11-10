import React from 'react'

function FailureDetail({ failure, onClose }) {
  return (
    <div className="failure-detail">
      <div className="detail-header">
        <div>
          <h2>{failure.job_name} #{failure.build_number}</h2>
          <p className="detail-timestamp">
            {new Date(failure.timestamp).toLocaleString()}
          </p>
        </div>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      
      <div className="detail-content">
        <div className="detail-section">
          <div className="section-header">
            <h3>🎯 Root Cause</h3>
            <span className={`confidence-badge ${failure.confidence}`}>
              {failure.confidence?.toUpperCase() || 'UNKNOWN'} CONFIDENCE
            </span>
          </div>
          <div className="section-content">
            <p>{failure.root_cause}</p>
          </div>
        </div>
        
        <div className="detail-section">
          <h3>💡 Suggested Fix</h3>
          <div className="section-content fix-content">
            <pre>{failure.suggested_fix}</pre>
          </div>
        </div>
        
        <div className="detail-actions">
          <button className="action-btn primary">
            📋 Copy Fix to Clipboard
          </button>
          <button className="action-btn">
            🔗 View Build in Jenkins
          </button>
        </div>
      </div>
    </div>
  )
}

export default FailureDetail
