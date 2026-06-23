import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, Legend, LineChart, Line,
} from 'recharts';
import { Hexagon, BarChart2, Trophy, Clock, Landmark, AlertTriangle, Medal, TrendingUp, MapPin } from 'lucide-react';

/* -- colour helpers -- */
const scoreColor = (score) => {
  if (score == null) return '#475569';
  if (score >= 70) return '#22c55e';
  if (score >= 45) return '#f59e0b';
  return '#ef4444';
};

const labelClass = (label) => {
  if (!label || label === 'No Data') return 'badge-nodata';
  return `badge-${label.toLowerCase()}`;
};

/* -- Custom tooltip for bar charts -- */
const CustomTooltip = ({ active, payload, label, unit = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-label">{label}</p>
      <p className="chart-tooltip-value">
        {typeof payload[0].value === 'number'
          ? payload[0].value.toLocaleString()
          : payload[0].value}
        {unit}
      </p>
    </div>
  );
};

/* -- Stat card -- */
const StatCard = ({ label, value, sub, color }) => (
  <div className="dash-stat-card" style={{ '--accent': color }}>
    <div className="dash-stat-value" style={{ color }}>{value}</div>
    <div className="dash-stat-label">{label}</div>
    {sub && <div className="dash-stat-sub">{sub}</div>}
  </div>
);

/* ======================================================== */
const Dashboard = () => {
  const [healthData, setHealthData] = useState([]);
  const [councillorData, setCouncillorData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [sortKey, setSortKey] = useState('health_score');
  const [sortDir, setSortDir] = useState('desc');

  useEffect(() => {
    Promise.all([
      fetch('/api/health-scores/').then(r => r.json()),
      fetch('/api/councillors/').then(r => r.json()),
      fetch('/api/trends/').then(r => r.json()),
    ]).then(([health, council, trends]) => {
      setHealthData(health);
      setCouncillorData(council);
      setTrendData(trends);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="dash-loading">
      <div className="dash-spinner" />
      <p>Loading ward data...</p>
    </div>
  );

  /* -- Derived stats -- */
  const withScores = healthData.filter(w => w.health_score != null);
  const goodCount     = withScores.filter(w => w.label === 'Good').length;
  const moderateCount = withScores.filter(w => w.label === 'Moderate').length;
  const poorCount     = withScores.filter(w => w.label === 'Poor').length;
  const avgScore      = withScores.length
    ? Math.round(withScores.reduce((s, w) => s + w.health_score, 0) / withScores.length)
    : '--';

  const top5    = [...withScores].sort((a, b) => b.health_score - a.health_score).slice(0, 5);
  const bottom5 = [...withScores].sort((a, b) => a.health_score - b.health_score).slice(0, 5);

  /* -- Sorted leaderboard -- */
  const sortedLeaderboard = [...healthData].sort((a, b) => {
    const av = a[sortKey] ?? (sortDir === 'desc' ? -Infinity : Infinity);
    const bv = b[sortKey] ?? (sortDir === 'desc' ? -Infinity : Infinity);
    return sortDir === 'desc' ? bv - av : av - bv;
  });

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  /* -- Chart data -- */
  const resolutionChartData = [...withScores]
    .sort((a, b) => (b.metrics?.avg_resolution_days ?? 0) - (a.metrics?.avg_resolution_days ?? 0))
    .map(w => ({
      name: w.ward_name,
      days: w.metrics?.avg_resolution_days ?? 0,
      score: w.health_score,
    }));

  const deliberationChartData = [...councillorData]
    .sort((a, b) => (b.per_capita_deliberations ?? 0) - (a.per_capita_deliberations ?? 0))
    .map(w => ({
      name: w.ward_name,
      perCapita: w.per_capita_deliberations ?? 0,
      score: w.engagement_score ?? 0,
    }));

  const healthBarData = [...withScores]
    .sort((a, b) => b.health_score - a.health_score)
    .map(w => ({ name: w.ward_name, score: w.health_score, label: w.label }));

  return (
    <div className="dashboard">
      {/* -- Sidebar -- */}
      <aside className="dash-sidebar">
        <div className="dash-brand">
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </div>
        <nav className="dash-nav">
          {[
            { key: 'overview',       icon: <BarChart2 size={18} />, label: 'Overview' },
            { key: 'leaderboard',    icon: <Trophy size={18} />, label: 'Leaderboard' },
            { key: 'resolution',     icon: <Clock size={18} />, label: 'Resolution Speed' },
            { key: 'engagement',     icon: <Landmark size={18} />, label: 'Civic Engagement' },
            { key: 'trends',         icon: <TrendingUp size={18} />, label: 'Historical Trends' },
          ].map(tab => (
            <button
              key={tab.key}
              id={`dash-tab-${tab.key}`}
              className={`dash-nav-item ${activeTab === tab.key ? 'dash-nav-active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
        <Link to="/complaints-map" className="dash-nav-item" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.85rem', borderRadius: 8 }}>
          <MapPin size={18} /> Complaint Map
        </Link>
        <a href="/" className="dash-back-link" id="back-to-home">
          &lt; Back to Home
        </a>
      </aside>

      {/* Main */}
      <main className="dash-main">
        <header className="dash-header">
          <div>
            <h1 className="dash-title">
              {activeTab === 'overview'    && 'City Overview'}
              {activeTab === 'leaderboard' && 'Ward Leaderboard'}
              {activeTab === 'resolution'  && 'Resolution Speed'}
              {activeTab === 'engagement'  && 'Civic Engagement'}
              {activeTab === 'trends'      && 'Historical Trends'}
            </h1>
            <p className="dash-subtitle">Mumbai * 24 Wards * 2019-2023 Data</p>
          </div>
        </header>

        {/* === OVERVIEW TAB === */}
        {activeTab === 'overview' && (
          <div className="dash-content">
            {/* Stat Cards */}
            <div className="dash-stats-row">
              <StatCard label="Avg Health Score" value={avgScore} sub="across all 24 wards" color="#818cf8" />
              <StatCard label="Good Wards"     value={goodCount}     sub="score >= 70" color="#22c55e" />
              <StatCard label="Moderate Wards" value={moderateCount} sub="score 45-69" color="#f59e0b" />
              <StatCard label="Poor Wards"     value={poorCount}     sub="score < 45"  color="#ef4444" />
            </div>

            {/* Top vs Bottom */}
            <div className="dash-two-col">
              <div className="dash-card">
                <h3 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Trophy size={20} color="#fbbf24" /> Top 5 Wards
                </h3>
                {top5.map((w, i) => (
                  <div key={w.ward_name} className="mini-ward-row">
                    <span className="mini-rank">
                      {i === 0 ? <Medal size={16} color="#fbbf24" /> : i === 1 ? <Medal size={16} color="#94a3b8" /> : i === 2 ? <Medal size={16} color="#b45309" /> : i + 1}
                    </span>
                    <span className="mini-name">Ward {w.ward_name}</span>
                    <span className={`table-badge ${labelClass(w.label)}`}>{w.label}</span>
                    <span className="mini-score" style={{ color: scoreColor(w.health_score) }}>
                      {Math.round(w.health_score)}
                    </span>
                  </div>
                ))}
              </div>
              <div className="dash-card">
                <h3 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={20} color="#ef4444" /> Bottom 5 Wards
                </h3>
                {bottom5.map((w, i) => (
                  <div key={w.ward_name} className="mini-ward-row">
                    <span className="mini-rank" style={{ color: '#ef4444' }}>{i + 1}</span>
                    <span className="mini-name">Ward {w.ward_name}</span>
                    <span className={`table-badge ${labelClass(w.label)}`}>{w.label}</span>
                    <span className="mini-score" style={{ color: scoreColor(w.health_score) }}>
                      {Math.round(w.health_score)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Health Score Bar Chart -- all 24 wards */}
            <div className="dash-card dash-card-full">
              <h3 className="dash-card-title">Health Score -- All 24 Wards</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={healthBarData} margin={{ top: 8, right: 16, left: 0, bottom: 32 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip unit=" pts" />} />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {healthBarData.map((entry) => (
                      <Cell key={entry.name} fill={scoreColor(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* === LEADERBOARD TAB === */}
        {activeTab === 'leaderboard' && (
          <div className="dash-content">
            <div className="dash-card dash-card-full">
              <div className="table-scroll">
                <table className="councillor-table" id="ward-leaderboard-table">
                  <thead>
                    <tr>
                      <th className="th-rank">#</th>
                      <th>Ward</th>
                      <th className="th-sortable" onClick={() => handleSort('health_score')} id="sort-health">
                        Health Score {sortKey === 'health_score' ? (sortDir === 'desc' ? 'v' : '^') : '<->'}
                      </th>
                      <th className="th-sortable" onClick={() => handleSort('label')} id="sort-label">
                        Status
                      </th>
                      <th className="th-sortable" onClick={() => handleSort('metrics.total_complaints')} id="sort-complaints">
                        Complaints
                      </th>
                      <th className="th-sortable" onClick={() => handleSort('metrics.avg_resolution_days')} id="sort-resolution">
                        Avg Days
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedLeaderboard.map((w, i) => (
                      <tr key={w.ward_name} className={i < 3 ? 'tr-top' : ''}>
                        <td className="td-rank" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {i === 0 ? <Medal size={18} color="#fbbf24" /> : i === 1 ? <Medal size={18} color="#94a3b8" /> : i === 2 ? <Medal size={18} color="#b45309" /> : i + 1}
                        </td>
                        <td>
                          <div className="ward-cell">
                            <span className="ward-cell-name">Ward {w.ward_name}</span>
                            <span className="ward-cell-no">No. {w.ward_no}</span>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                            <div style={{
                              width: `${Math.round(w.health_score ?? 0)}%`,
                              maxWidth: 80,
                              height: 6,
                              background: scoreColor(w.health_score),
                              borderRadius: 100,
                              transition: 'width 0.4s',
                            }} />
                            <span className="td-num" style={{ color: scoreColor(w.health_score) }}>
                              {w.health_score != null ? Math.round(w.health_score) : '--'}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`table-badge ${labelClass(w.label)}`}>{w.label}</span>
                        </td>
                        <td className="td-num">{w.metrics?.total_complaints?.toLocaleString() ?? '--'}</td>
                        <td className="td-num">{w.metrics?.avg_resolution_days ?? '--'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* === RESOLUTION TAB === */}
        {activeTab === 'resolution' && (
          <div className="dash-content">
            <div className="dash-card dash-card-full">
              <h3 className="dash-card-title">Average Complaint Resolution Days by Ward</h3>
              <p className="dash-card-sub">Wards at the top have the slowest resolution times -- these need the most urgent intervention.</p>
              <ResponsiveContainer width="100%" height={420}>
                <BarChart
                  data={resolutionChartData}
                  layout="vertical"
                  margin={{ top: 8, right: 48, left: 32, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} unit=" days" />
                  <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={36} />
                  <Tooltip content={<CustomTooltip unit=" days" />} />
                  <Bar dataKey="days" radius={[0, 4, 4, 0]}>
                    {resolutionChartData.map(entry => (
                      <Cell key={entry.name} fill={scoreColor(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* === ENGAGEMENT TAB === */}
        {activeTab === 'engagement' && (
          <div className="dash-content">
            <div className="dash-card dash-card-full">
              <h3 className="dash-card-title">Per Capita Deliberations by Ward</h3>
              <p className="dash-card-sub">Higher deliberation per capita indicates more active councillor engagement with constituents.</p>
              <ResponsiveContainer width="100%" height={360}>
                <BarChart
                  data={deliberationChartData}
                  margin={{ top: 8, right: 16, left: 0, bottom: 36 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="perCapita" radius={[4, 4, 0, 0]} name="Per Capita Deliberations">
                    {deliberationChartData.map(entry => (
                      <Cell
                        key={entry.name}
                        fill={entry.score >= 70 ? '#22c55e' : entry.score >= 40 ? '#f59e0b' : '#ef4444'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
        {/* === TRENDS TAB === */}
        {activeTab === 'trends' && (
          <div className="dash-content">
            <div className="dash-card dash-card-full">
              <h3 className="dash-card-title">Complaint Volume Trend</h3>
              <p className="dash-card-sub">Total civic complaints registered across Mumbai wards from 2019 to 2025.</p>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                  <XAxis dataKey="year" tick={{ fill: '#64748b' }} />
                  <YAxis tick={{ fill: '#64748b' }} />
                  <Tooltip content={<CustomTooltip unit=" complaints" />} />
                  <Line type="monotone" dataKey="total_complaints" name="Total Complaints" stroke="#818cf8" strokeWidth={3} dot={{ r: 4, fill: '#818cf8' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div className="dash-card dash-card-full">
              <h3 className="dash-card-title">Average Resolution Speed</h3>
              <p className="dash-card-sub">Average days taken to resolve a complaint citywide (2019-2025).</p>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                  <XAxis dataKey="year" tick={{ fill: '#64748b' }} />
                  <YAxis tick={{ fill: '#64748b' }} />
                  <Tooltip content={<CustomTooltip unit=" days" />} />
                  <Line type="monotone" dataKey="avg_resolution_days" name="Avg Resolution Days" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4, fill: '#f59e0b' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
