import React, { useState, useEffect } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown, Medal } from 'lucide-react';
import API_BASE from '../config';

const SORT_KEYS = {
  engagement: 'engagement_score',
  deliberations: 'total_deliberations',
  percapita: 'per_capita_deliberations',
  councillors: 'avg_councillors',
};

const CouncillorTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('engagement');
  const [sortDir, setSortDir] = useState('desc');

  useEffect(() => {
    fetch(`${API_BASE}/councillors/`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = [...data].sort((a, b) => {
    const field = SORT_KEYS[sortKey];
    const av = a[field] ?? -Infinity;
    const bv = b[field] ?? -Infinity;
    return sortDir === 'desc' ? bv - av : av - bv;
  });

  const getEngagementBadge = (score) => {
    if (score === null || score === undefined) return { label: 'No Data', cls: 'badge-nodata' };
    if (score >= 70) return { label: 'High', cls: 'badge-good' };
    if (score >= 40) return { label: 'Medium', cls: 'badge-moderate' };
    return { label: 'Low', cls: 'badge-poor' };
  };

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className="sort-icon sort-inactive" style={{ display: 'inline-flex', verticalAlign: 'middle' }}><ArrowUpDown size={14} /></span>;
    return <span className="sort-icon sort-active" style={{ display: 'inline-flex', verticalAlign: 'middle' }}>{sortDir === 'desc' ? <ArrowDown size={14} /> : <ArrowUp size={14} />}</span>;
  };

  if (loading) return (
    <div className="table-loading">
      <span className="locate-spinner" style={{ width: 24, height: 24, borderWidth: 3 }} />
    </div>
  );

  return (
    <div className="councillor-table-wrapper">
      <div className="table-scroll">
        <table className="councillor-table" id="councillor-accountability-table">
          <thead>
            <tr>
              <th className="th-rank">#</th>
              <th>Ward</th>
              <th
                className="th-sortable"
                onClick={() => handleSort('councillors')}
                id="sort-councillors"
              >
                Avg Councillors <SortIcon col="councillors" />
              </th>
              <th
                className="th-sortable"
                onClick={() => handleSort('deliberations')}
                id="sort-deliberations"
              >
                Total Deliberations <SortIcon col="deliberations" />
              </th>
              <th
                className="th-sortable"
                onClick={() => handleSort('percapita')}
                id="sort-percapita"
              >
                Per Capita <SortIcon col="percapita" />
              </th>
              <th
                className="th-sortable"
                onClick={() => handleSort('engagement')}
                id="sort-engagement"
              >
                Engagement <SortIcon col="engagement" />
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => {
              const badge = getEngagementBadge(row.engagement_score);
              return (
                <tr key={row.ward_no} className={i < 3 ? 'tr-top' : ''}>
                  <td className="td-rank" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {i === 0 ? <Medal size={18} color="#fbbf24" /> : i === 1 ? <Medal size={18} color="#94a3b8" /> : i === 2 ? <Medal size={18} color="#b45309" /> : i + 1}
                  </td>
                  <td>
                    <div className="ward-cell">
                      <span className="ward-cell-name">{row.ward_name}</span>
                      <span className="ward-cell-no">No. {row.ward_no}</span>
                    </div>
                  </td>
                  <td className="td-num">{row.avg_councillors ?? '—'}</td>
                  <td className="td-num">{row.total_deliberations?.toLocaleString() ?? '—'}</td>
                  <td className="td-num">{row.per_capita_deliberations ?? '—'}</td>
                  <td>
                    <div className="engagement-cell">
                      <span className={`table-badge ${badge.cls}`}>{badge.label}</span>
                      <div className="engagement-bar-track">
                        <div
                          className="engagement-bar-fill"
                          style={{
                            width: `${row.engagement_score ?? 0}%`,
                            background: row.engagement_score >= 70
                              ? '#22c55e'
                              : row.engagement_score >= 40
                                ? '#f59e0b'
                                : '#ef4444',
                          }}
                        />
                      </div>
                      <span className="engagement-score-num">
                        {row.engagement_score?.toFixed(0) ?? '—'}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CouncillorTable;
