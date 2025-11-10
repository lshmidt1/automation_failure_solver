import React from 'react'

function Stats({ failures }) {
  const totalFailures = failures.length
  
  const confidenceCounts = failures.reduce((acc, failure) => {
    const conf = failure.confidence || 'unknown'
    acc[conf] = (acc[conf] || 0) + 1
    return acc
  }, {})
  
  const highConfidence = confidenceCounts.high || 0
  const mediumConfidence = confidenceCounts.medium || 0
  const lowConfidence = confidenceCounts.low || 0

  return (
    <div className="stats">
      <div className="stat-card">
        <div className="stat-value">{totalFailures}</div>
        <div className="stat-label">Total Analyses</div>
      </div>
      
      <div className="stat-card high">
        <div className="stat-value">{highConfidence}</div>
        <div className="stat-label">High Confidence</div>
      </div>
      
      <div className="stat-card medium">
        <div className="stat-value">{mediumConfidence}</div>
        <div className="stat-label">Medium Confidence</div>
      </div>
      
      <div className="stat-card low">
        <div className="stat-value">{lowConfidence}</div>
        <div className="stat-label">Low Confidence</div>
      </div>
    </div>
  )
}

export default Stats