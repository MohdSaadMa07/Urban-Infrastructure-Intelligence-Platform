import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart,
  ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ArrowLeft, Filter, Hexagon, Search } from 'lucide-react';
import API_BASE from '../config';

const COLORS = ['#1686e8', '#2337ad', '#f09b7d', '#9d54a9', '#e576be', '#8e78d5'];
const CATEGORY_ORDER = ['pothole', 'garbage', 'water', 'drainage', 'streetlight', 'road'];
const formatNumber = value => Number(value || 0).toLocaleString();
const average = values => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;

function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="powerbi-tooltip"><strong>{label || payload[0].name}</strong>{payload.map(item => <div key={item.dataKey}>{item.name || item.dataKey}: {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}</div>)}</div>;
}

function Metric({ label, value, detail }) {
  return <div className="powerbi-metric"><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}

function PowerBIInsights() {
  const [health, setHealth] = useState([]);
  const [councillors, setCouncillors] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [activePage, setActivePage] = useState('intelligence');
  const [selectedWard, setSelectedWard] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/health-scores/`).then(response => response.json()),
      fetch(`${API_BASE}/councillors/`).then(response => response.json()),
      fetch(`${API_BASE}/complaints/?page_size=500`).then(response => response.json()),
    ]).then(([healthData, councillorData, complaintData]) => {
      setHealth(healthData);
      setCouncillors(councillorData);
      setComplaints(Array.isArray(complaintData) ? complaintData : complaintData.results || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filteredComplaints = useMemo(() => complaints.filter(complaint =>
    (!selectedWard || complaint.ward_name === selectedWard) &&
    (selectedCategory === 'all' || complaint.category.toLowerCase().includes(selectedCategory))
  ), [complaints, selectedCategory, selectedWard]);
  const categoryData = useMemo(() => CATEGORY_ORDER.map(category => ({ name: category, value: filteredComplaints.filter(item => item.category.toLowerCase().includes(category)).length })).filter(item => item.value > 0), [filteredComplaints]);
  const wardData = useMemo(() => health.map(ward => ({ name: ward.ward_name, complaints: ward.metrics?.total_complaints || 0, resolved: ward.metrics?.closed_complaints || 0, resolution: ward.metrics?.avg_resolution_days || 0, score: ward.health_score || 0 })), [health]);
  const civicData = useMemo(() => councillors.map(ward => ({ name: ward.ward_name, deliberations: ward.per_capita_deliberations || 0, score: health.find(item => item.ward_name === ward.ward_name)?.health_score || 0, complaints: health.find(item => item.ward_name === ward.ward_name)?.metrics?.total_complaints || 0 })), [councillors, health]);
  const selectedHealth = health.find(ward => ward.ward_name === selectedWard) || health[0];
  const selectedComplaints = complaints.filter(item => item.ward_name === selectedHealth?.ward_name);
  const statusData = ['open', 'in_progress', 'resolved'].map(status => ({ name: status.replace('_', ' '), value: selectedComplaints.filter(item => item.status === status).length })).filter(item => item.value);
  const detailCategoryData = CATEGORY_ORDER.map(category => ({ name: category, value: selectedComplaints.filter(item => item.category.toLowerCase().includes(category)).length })).filter(item => item.value);
  const pages = [
    { id: 'report-pages', label: 'Power BI Report Pages' },
    { id: 'overview', label: 'Ward Overview' },
    { id: 'intelligence', label: 'Complaint Intelligence' },
    { id: 'civic', label: 'Civic Performance' },
    { id: 'investigation', label: 'Complaint Investigation' },
    { id: 'details', label: 'Ward Details' },
  ];

  if (loading) return <div className="powerbi-loading">Loading UrbanIQ report data...</div>;
  return (
    <div className="powerbi-shell">
      <header className="powerbi-header"><Link to="/dashboard" className="powerbi-brand"><Hexagon size={22} /> UrbanIQ</Link><div><span className="powerbi-kicker">Power BI report visuals · live UrbanIQ analytics</span><h1>{pages.find(page => page.id === activePage)?.label}</h1></div><Link to="/" className="powerbi-back"><ArrowLeft size={16} /> Home</Link></header>
      <nav className="powerbi-tabs" aria-label="Analytics pages">{pages.map(page => <button key={page.id} className={activePage === page.id ? 'active' : ''} onClick={() => setActivePage(page.id)}>{page.label}</button>)}</nav>
      {activePage !== 'report-pages' && <section className="powerbi-controls"><Filter size={16} /><label>Ward <select value={selectedWard} onChange={event => setSelectedWard(event.target.value)}><option value="">All wards</option>{health.map(ward => <option key={ward.ward_name}>{ward.ward_name}</option>)}</select></label><label>Category <select value={selectedCategory} onChange={event => setSelectedCategory(event.target.value)}><option value="all">All categories</option>{CATEGORY_ORDER.map(category => <option key={category} value={category}>{category}</option>)}</select></label><span className="powerbi-filter-note"><Search size={14} /> Filters affect the live report visuals</span></section>}

      {activePage === 'report-pages' && <section className="powerbi-report-pages"><div className="powerbi-report-intro"><span className="powerbi-made-with">Created with Microsoft Power BI</span><h2>Power BI report exports</h2><p>These five pages are the supplied Power BI visual exports. The other tabs are interactive UrbanIQ views that use the same reporting themes with current data from the health-score, councillor, and complaint APIs. Filters apply to the live views, not to these exported images.</p></div><div className="powerbi-report-gallery">{[
        ['first.png', 'Ward Overview', 'A high-level view of complaint volume, category mix, ward demand, and resolution performance.'],
        ['second.png', 'Complaint Intelligence', 'A comparison page for finding issue patterns by ward and category.'],
        ['third.png', 'Civic Performance', 'Connects civic engagement, ward health scores, complaint load, and resolution speed.'],
        ['fourth.png', 'Complaint Investigation', 'Supports operational drill-through into individual complaint records and their status.'],
        ['fifth.png', 'Ward Details', 'Focuses on a selected ward’s health score, complaint status, issue mix, and service performance.'],
      ].map(([image, title, description]) => <figure className="powerbi-report-card" key={image}><img src={`/powerbi-pages/${image}`} alt={`${title} Power BI report page`} loading="lazy" /><figcaption><h3>{title}</h3><p>{description}</p></figcaption></figure>)}</div><div className="powerbi-source-note"><strong>How to read this area:</strong> exported pages preserve the original Power BI design and values at export time; live tabs refresh from UrbanIQ’s backend and may therefore differ from the screenshots.</div></section>}

      {activePage === 'overview' && <div className="powerbi-grid"><Metric label="Total complaints" value={formatNumber(filteredComplaints.length)} detail="Current portal records" /><Metric label="Average resolution days" value={average(wardData.map(item => item.resolution)).toFixed(1)} detail="Latest ward metrics" /><Metric label="Resolved complaints" value={formatNumber(filteredComplaints.filter(item => item.status === 'resolved').length)} detail="Status-tracked records" /><Metric label="Resolution rate" value={`${filteredComplaints.length ? Math.round(filteredComplaints.filter(item => item.status === 'resolved').length / filteredComplaints.length * 100) : 0}%`} detail="Resolved / total" /><div className="powerbi-panel wide"><h2>Complaint distribution by category</h2><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={categoryData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={3}>{categoryData.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip content={<ChartTip />} /><Legend /></PieChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Total complaints by ward</h2><ResponsiveContainer width="100%" height={330}><BarChart data={wardData} layout="vertical" margin={{ left: 12, right: 16 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={42} /><Tooltip content={<ChartTip />} /><Bar dataKey="complaints" fill="#1686e8" /></BarChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Ward resolution rate</h2><ResponsiveContainer width="100%" height={330}><BarChart data={wardData.map(item => ({ ...item, rate: item.complaints ? item.resolved / item.complaints : 0 }))} layout="vertical" margin={{ left: 12, right: 16 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 1]} tickFormatter={value => `${value * 100}%`} /><YAxis dataKey="name" type="category" width={42} /><Tooltip content={<ChartTip />} /><Bar dataKey="rate" name="Resolution rate" fill="#2337ad" /></BarChart></ResponsiveContainer></div></div>}

      {activePage === 'intelligence' && <div className="powerbi-grid"><Metric label="Total complaints" value={formatNumber(filteredComplaints.length)} detail="Current portal records" /><Metric label="Average resolution days" value={average(wardData.map(item => item.resolution)).toFixed(1)} detail="Latest ward metrics" /><Metric label="Resolved complaints" value={formatNumber(filteredComplaints.filter(item => item.status === 'resolved').length)} detail="Status-tracked records" /><Metric label="Resolution rate" value={`${filteredComplaints.length ? Math.round(filteredComplaints.filter(item => item.status === 'resolved').length / filteredComplaints.length * 100) : 0}%`} detail="Resolved / total" /><div className="powerbi-panel wide"><h2>Complaint distribution by category</h2><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={categoryData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={3}>{categoryData.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip content={<ChartTip />} /><Legend /></PieChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Total complaints by ward</h2><ResponsiveContainer width="100%" height={330}><BarChart data={wardData} layout="vertical" margin={{ left: 12, right: 16 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={42} /><Tooltip content={<ChartTip />} /><Bar dataKey="complaints" fill="#1686e8" /></BarChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Ward resolution rate</h2><ResponsiveContainer width="100%" height={330}><BarChart data={wardData.map(item => ({ ...item, rate: item.complaints ? item.resolved / item.complaints : 0 }))} layout="vertical" margin={{ left: 12, right: 16 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 1]} tickFormatter={value => `${value * 100}%`} /><YAxis dataKey="name" type="category" width={42} /><Tooltip content={<ChartTip />} /><Bar dataKey="rate" name="Resolution rate" fill="#2337ad" /></BarChart></ResponsiveContainer></div></div>}

      {activePage === 'civic' && <div className="powerbi-grid single-focus"><div className="powerbi-panel wide"><h2>Civic engagement vs ward health</h2><p className="powerbi-explainer">Each bubble is a ward. Moving right means more per-capita deliberations; moving up means a stronger health score. Bubble size reflects complaint volume.</p><ResponsiveContainer width="100%" height={520}><ScatterChart margin={{ top: 20, right: 24, bottom: 24, left: 8 }}><CartesianGrid /><XAxis type="number" dataKey="deliberations" name="Per-capita deliberations" /><YAxis type="number" dataKey="score" name="Health score" domain={[0, 100]} /><Tooltip cursor={{ strokeDasharray: '3 3' }} content={<ChartTip />} /><Scatter data={civicData} fill="#1686e8">{civicData.map(item => <Cell key={item.name} r={Math.max(7, Math.min(24, item.complaints / 2))} />)}</Scatter></ScatterChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Ward health scores</h2><ResponsiveContainer width="100%" height={380}><BarChart data={[...wardData].sort((a, b) => b.score - a.score)} layout="vertical" margin={{ left: 10, right: 18 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} /><YAxis dataKey="name" type="category" width={42} /><Tooltip content={<ChartTip />} /><Bar dataKey="score" fill="#1686e8" /></BarChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Average resolution days</h2><ResponsiveContainer width="100%" height={380}><BarChart data={wardData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" angle={-45} textAnchor="end" height={70} /><YAxis /><Tooltip content={<ChartTip />} /><Bar dataKey="resolution" fill="#f09b7d" /></BarChart></ResponsiveContainer></div></div>}

      {activePage === 'investigation' && <div className="powerbi-panel investigation-panel"><h2>Complaint investigation flow</h2><p className="powerbi-explainer">Use the controls above to narrow the investigation from all complaints to one ward and category, then inspect the resulting records.</p><div className="investigation-flow"><div><strong>{filteredComplaints.length}</strong><span>Total complaints</span></div><div><strong>{new Set(filteredComplaints.map(item => item.ward_name)).size}</strong><span>Wards represented</span></div><div><strong>{categoryData.length}</strong><span>Categories</span></div></div><div className="investigation-table"><div className="investigation-row heading"><span>ID</span><span>Ward</span><span>Category</span><span>Status</span><span>Created</span></div>{filteredComplaints.slice(0, 50).map(item => <div className="investigation-row" key={item.id}><span>#{item.id}</span><span>{item.ward_name}</span><span>{item.category}</span><span className={`status-${item.status}`}>{item.status.replace('_', ' ')}</span><span>{new Date(item.created_at).toLocaleDateString()}</span></div>)}</div></div>}

      {activePage === 'details' && selectedHealth && <div className="powerbi-grid ward-detail-grid"><Metric label="Ward health score" value={Math.round(selectedHealth.health_score || 0)} detail={selectedHealth.label} /><Metric label="Total complaints" value={formatNumber(selectedHealth.metrics?.total_complaints)} detail={`Ward ${selectedHealth.ward_name}`} /><Metric label="Resolution rate" value={`${selectedHealth.metrics?.total_complaints ? Math.round(selectedHealth.metrics.closed_complaints / selectedHealth.metrics.total_complaints * 100) : 0}%`} detail="Closed complaints / total" /><Metric label="Average resolution" value={`${selectedHealth.metrics?.avg_resolution_days || 0}`} detail="Days" /><div className="powerbi-panel"><h2>Complaints by status</h2><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={statusData} dataKey="value" nameKey="name" innerRadius={65} outerRadius={105}>{statusData.map((item, index) => <Cell key={item.name} fill={['#1686e8', '#2337ad', '#e66b35'][index]} />)}</Pie><Tooltip content={<ChartTip />} /><Legend /></PieChart></ResponsiveContainer></div><div className="powerbi-panel"><h2>Complaints by category</h2><ResponsiveContainer width="100%" height={300}><BarChart data={detailCategoryData} layout="vertical" margin={{ left: 20, right: 20 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={70} /><Tooltip content={<ChartTip />} /><Bar dataKey="value" fill="#1686e8" /></BarChart></ResponsiveContainer></div></div>}
    </div>
  );
}

export default PowerBIInsights;
