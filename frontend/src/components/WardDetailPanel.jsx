import React from 'react';

const WardDetailPanel = ({ ward, onClose }) => {
  if (!ward) return null;

  const { ward_name, ward_no, health_score, label, metrics, breakdown } = ward;

  const labelClass = (label || 'nodata').toLowerCase();

  const getScoreBarColor = (value) => {
    if (value >= 0.7) return '#22c55e';
    if (value >= 0.4) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <>
      <div className="panel-overlay" onClick={onClose}></div>
      <div className="ward-panel">
        <button className="panel-close" onClick={onClose}>✕</button>

        {/* Header */}
        <div className="panel-header">
          <div className="panel-ward-name">Ward {ward_name}</div>
          <div className="panel-ward-no">Ward No. {ward_no}</div>
        </div>

        {/* Health Score */}
        <div className="panel-score-section">
          <div className={`panel-score-ring panel-score-${labelClass}`}>
            <span className="panel-score-value">
              {health_score != null ? Math.round(health_score) : '—'}
            </span>
          </div>
          <div className={`panel-score-label health-badge-${labelClass}`}>
            {label || 'No Data'}
          </div>
          <div className="panel-score-caption">Infrastructure Health Score</div>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="panel-metrics">
            <h4 className="panel-section-title">Key Metrics</h4>
            <div className="panel-metric-row">
              <span className="metric-name">Total Complaints</span>
              <span className="metric-value">{metrics.total_complaints?.toLocaleString()}</span>
            </div>
            <div className="panel-metric-row">
              <span className="metric-name">Per Capita Complaints</span>
              <span className="metric-value">{metrics.per_capita_complaints?.toLocaleString()}</span>
            </div>
            <div className="panel-metric-row">
              <span className="metric-name">Avg Resolution Days</span>
              <span className="metric-value">{metrics.avg_resolution_days}</span>
            </div>
            <div className="panel-metric-row">
              <span className="metric-name">Deliberations</span>
              <span className="metric-value">{metrics.total_deliberations?.toLocaleString()}</span>
            </div>
            <div className="panel-metric-row">
              <span className="metric-name">Closed Complaints</span>
              <span className="metric-value">{metrics.closed_complaints?.toLocaleString()}</span>
            </div>
            <div className="panel-metric-row">
              <span className="metric-name">Escalated Complaints</span>
              <span className="metric-value">{metrics.escalated_complaints?.toLocaleString()}</span>
            </div>
          </div>
        )}

        {/* Score Breakdown */}
        {breakdown && (
          <div className="panel-breakdown">
            <h4 className="panel-section-title">Score Breakdown</h4>
            <div className="breakdown-bar-item">
              <div className="breakdown-bar-label">
                <span>Per Capita Complaints</span>
                <span>{Math.round((breakdown.complaint_score || 0) * 100)}%</span>
              </div>
              <div className="breakdown-bar-track">
                <div
                  className="breakdown-bar-fill"
                  style={{
                    width: `${(breakdown.complaint_score || 0) * 100}%`,
                    background: getScoreBarColor(breakdown.complaint_score || 0),
                  }}
                ></div>
              </div>
            </div>
            <div className="breakdown-bar-item">
              <div className="breakdown-bar-label">
                <span>Resolution Speed</span>
                <span>{Math.round((breakdown.resolution_score || 0) * 100)}%</span>
              </div>
              <div className="breakdown-bar-track">
                <div
                  className="breakdown-bar-fill"
                  style={{
                    width: `${(breakdown.resolution_score || 0) * 100}%`,
                    background: getScoreBarColor(breakdown.resolution_score || 0),
                  }}
                ></div>
              </div>
            </div>
            <div className="breakdown-bar-item">
              <div className="breakdown-bar-label">
                <span>Civic Engagement</span>
                <span>{Math.round((breakdown.deliberation_score || 0) * 100)}%</span>
              </div>
              <div className="breakdown-bar-track">
                <div
                  className="breakdown-bar-fill"
                  style={{
                    width: `${(breakdown.deliberation_score || 0) * 100}%`,
                    background: getScoreBarColor(breakdown.deliberation_score || 0),
                  }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {!metrics && (
          <div className="panel-no-data">
            <p>No civic metrics data available for this ward.</p>
          </div>
        )}
      </div>
    </>
  );
};

export default WardDetailPanel;
