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
const POWER_BI_EMBED_URL = 'https://app.powerbi.com/reportEmbed?reportId=d1c0ac68-01f9-413c-9d35-92a292639fa2&autoAuth=true&ctid=76bed47f-8633-49b2-8de1-35950dd0251c&actionBarEnabled=true';
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
  const [activePage, setActivePage] = useState('overview');
  const [selectedWard, setSelectedWard] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // This route intentionally displays static Power BI exports. Do not fetch
    // live API data here: it is neither used nor required to read the reports.
    setLoading(false);
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
    { id: 'overview', label: 'Ward Overview' },
    { id: 'intelligence', label: 'Complaint Intelligence' },
    { id: 'civic', label: 'Civic Performance' },
    { id: 'investigation', label: 'Complaint Investigation' },
    { id: 'details', label: 'Ward Details' },
  ];

  const reports = {
    overview: { image: 'first.png', summary: 'An at-a-glance view of civic complaint demand and service outcomes across Mumbai wards.', charts: [['Total complaints', 'The total number of complaints in scope, showing overall service demand.'], ['Average resolution days', 'The typical time taken to close a complaint; lower values mean faster service delivery.'], ['Resolved complaints', 'The count of completed complaints, showing the volume of finished work.'], ['Resolution rate', 'Resolved complaints as a share of all complaints; use it to compare follow-through between wards.'], ['Complaint distribution by category', 'Shows which issue types, such as roads, water, garbage, drainage, or streetlights, generate the greatest demand.'], ['Total complaints by ward', 'Compares complaint burden across wards and identifies high-demand areas.'], ['Ward resolution rate', 'Compares how effectively each ward closes the complaints it receives.']] },
    intelligence: { image: 'second.png', summary: 'A ward-by-category comparison page with an explicit performance ranking and category-level service-speed view.', charts: [['Category distribution by ward', 'The matrix shows the count of drainage, garbage, pothole, road, streetlight, and water complaints for every ward, with a total column.'], ['Ward health scores', 'A horizontal ranking of average health score by ward.'], ['Average resolution days by category', 'A horizontal comparison of average time to resolve each complaint category.'], ['Key data pattern', 'The matrix is evenly distributed by ward, while the category and performance charts expose the meaningful differences.']] },
    civic: { image: 'third.png', summary: 'A single scatter chart showing the relationship between civic participation and ward health.', charts: [['Civic engagement vs ward health', 'Each coloured bubble is a ward; horizontal position is average per-capita deliberations and vertical position is average health score.'], ['Bubble size', 'Bubble area represents the third encoded measure in the Power BI scatter visual, letting larger wards stand out visually.'], ['Clusters and outliers', 'The chart is designed to identify wards that depart from the main engagement/health cluster.']] },
    investigation: { image: 'fourth.png', summary: 'A Power BI decomposition tree for tracing the total complaint count through connected dimensions.', charts: [['Total complaint root', 'The tree starts from the overall complaint count and progressively breaks it down.'], ['Ward branch', 'The first split chooses a ward, showing the count carried into the selected branch.'], ['Per-capita comparison branch', 'The next split selects a per-capita comparison value before the final category breakdown.'], ['Category endpoint', 'The end nodes show the category counts for the selected path.']] },
    details: { image: 'fifth.png', summary: 'A focused profile of one ward’s complaint load, service outcomes, and issue mix.', charts: [['Ward health score', 'A 0–100 summary score for the selected ward, combining service demand, resolution performance, and civic engagement.'], ['Total complaints', 'The selected ward’s complaint volume, indicating the scale of local demand.'], ['Resolution rate', 'The share of the ward’s complaints that have been closed; higher is better.'], ['Average resolution', 'The average number of days taken to resolve ward complaints; lower is better.'], ['Complaints by status', 'Splits complaints into open, in-progress, and resolved groups to show the active workload.'], ['Complaints by category', 'Shows the issue types residents report most often, supporting targeted planning.']] },
  };
  const report = reports[activePage];
  const visualReadings = {
    overview: {
      'Total complaints': 'The card displays 147, while the category visual is aggregated over 602 records; read the visual-level totals in their own filter context rather than treating them as a single denominator.',
      'Average resolution days': 'The displayed average is 6.20 days, a relatively quick overall turnaround for the card’s current context.',
      'Resolved complaints': 'Only 16 complaints are marked resolved in the KPI context.',
      'Resolution rate': 'At 10.88%, roughly one in nine complaints is resolved in the KPI context, signalling a large outstanding workload.',
      'Complaint distribution by category': 'Potholes lead with 183 complaints (30.4%), followed by garbage at 147 (24.42%). Together they account for 54.82% of the 602 category records; road is smallest at 34 (5.65%).',
      'Total complaints by ward': 'The wards shown are tightly clustered at about 25–26 records each, so the displayed sample is broadly even by ward rather than dominated by one location.',
      'Ward resolution rate': 'M/E is the clear outlier near 40%, with D next near 28%. Several displayed wards sit close to 10–20%, revealing uneven closure performance.',
    },
    intelligence: {
      'Category distribution by ward': 'The matrix totals 602 complaints: potholes lead with 183, followed by garbage at 147, water at 97, drainage at 74, streetlight at 67, and road at 34. Nearly every ward totals 25 records, with L and M/W at 26.',
      'Ward health scores': 'R/S is highest at roughly 78, followed by F/N near 70 and G/S near 68. The displayed lower end, L, sits around 45—about a 33-point spread.',
      'Average resolution days by category': 'Road is the slowest at 15 days. Pothole and streetlight are each about 12.5 days, water 10, and garbage roughly 6.5 days; road is the clear delay outlier.',
      'Key data pattern': 'The workload is very even across wards, but outcomes vary: health scores range from about 45 to 78 and category resolution time ranges from roughly 6.5 to 15 days.',
    },
    civic: {
      'Civic engagement vs ward health': 'Most wards cluster around 25–60 per-capita deliberations and health scores of 35–52. The plot also shows clear positive outliers near (58, 78) and (98, 68), plus a low-health outlier near (25, 14).',
      'Bubble size': 'Bubble size is visibly varied, with several large bubbles in the mid-range cluster; use it as the third measure rather than comparing only x and y position.',
      'Clusters and outliers': 'The upper-right points combine high participation with stronger health. The low point around a 14 health score is the strongest warning signal, even though its engagement is not the lowest.',
    },
    investigation: {
      'Total complaint root': 'The root shows 602 total complaints. It is the number that each decomposition branch explains.',
      'Ward branch': 'The selected path begins at Ward L, which has 26 complaints; other visible ward branches are mainly 25–26, so the record volume is balanced.',
      'Per-capita comparison branch': 'Within Ward L, the chosen branch is the per-capita comparison value 4,491, retaining all 26 selected records.',
      'Category endpoint': 'The 26 selected records end as pothole 9, garbage 7, drainage 4, road 3, water 2, and streetlight 1. Potholes make up 34.6% of this drilled-down path.',
    },
    details: {
      'Ward health score': 'The selected ward is B and its displayed average health score is 12.13, markedly low on the report’s health scale.',
      'Total complaints': 'Ward B has 25 complaints in the selected context.',
      'Resolution rate': 'The card shows 20.00%, which matches the 5 resolved complaints in the status donut.',
      'Average resolution': 'The displayed average is 21.00 days, much slower than the 6.20-day KPI on the overview page.',
      'Complaints by status': 'Of 25 complaints, 13 are open (52%), 7 are in progress (28%), and only 5 are resolved (20%). The open/in-progress backlog is therefore 80%.',
      'Complaints by category': 'Potholes lead with 9 of 25 complaints (36%). Garbage, streetlight, and water each have 4; drainage has 3 and road has 1. The detail table also shows 38.29 per-capita deliberations, 3.00 average councillors, and 95.86 total deliberations.',
    },
  };

  return (
    <main className="powerbi-shell">
      <header className="powerbi-header"><Link to="/dashboard" className="powerbi-brand"><Hexagon size={22} /> UrbanIQ</Link><div><span className="powerbi-kicker">Created with Microsoft Power BI</span><h1>{pages.find(page => page.id === activePage)?.label}</h1></div><Link to="/" className="powerbi-back"><ArrowLeft size={16} /> Home</Link></header>
      <nav className="powerbi-tabs" aria-label="Power BI report pages">{pages.map(page => <button key={page.id} className={activePage === page.id ? 'active' : ''} onClick={() => setActivePage(page.id)}>{page.label}</button>)}</nav>
      <section className="powerbi-static-report"><div className="powerbi-report-intro"><span className="powerbi-made-with">Created with Microsoft Power BI</span><h2>{pages.find(page => page.id === activePage)?.label}</h2><p>{report.summary} Use the live embedded report below; the original screenshot is retained as an archived visual reference.</p></div><section className="powerbi-embed" aria-label="Live Power BI dashboard"><iframe title="UrbanIQ Power BI dashboard" src={POWER_BI_EMBED_URL} allowFullScreen /></section><details className="powerbi-archive"><summary>View archived screenshot for this page</summary><figure className="powerbi-full-report"><img src={`/powerbi-pages/${report.image}`} alt={`${pages.find(page => page.id === activePage)?.label} archived Power BI report page`} loading="lazy" /><figcaption>Original Power BI report export retained in this project and Git history.</figcaption></figure></details><section className="powerbi-chart-guide"><h2>What this page shows</h2><div className="powerbi-chart-explanations">{report.charts.map(([title, description]) => <article key={title}><h3>{title}</h3><p>{description}</p><p className="powerbi-chart-reading"><strong>What the visual signals:</strong> {visualReadings[activePage][title]}</p></article>)}</div></section></section>
    </main>
  );

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
