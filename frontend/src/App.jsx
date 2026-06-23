import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { Map, BarChart2, Activity, ShieldCheck, Megaphone, Hexagon, ArrowDown, LogIn, UserPlus, User as UserIcon, LogOut, MessageSquare, Smartphone, Camera, MapPin, CheckCircle, ExternalLink, Search, Crosshair, TrendingUp } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { AuthProvider, useAuth } from './context/AuthContext';
import MumbaiMap from './components/MumbaiMap';
import WardDetailPanel from './components/WardDetailPanel';
import ComplaintModal from './components/ComplaintModal';
import CouncillorTable from './components/CouncillorTable';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import TrackComplaint from './pages/TrackComplaint';
import AdminPortal from './pages/AdminPortal';
import Login from './pages/Login';
import Signup from './pages/Signup';
import CouncillorPortal from './pages/CouncillorPortal';
import PublicDashboard from './pages/PublicDashboard';
import ComplaintsMap from './pages/ComplaintsMap';
import './App.css';

/* --- Navbar Auth Actions --- */
function NavAuthActions() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    const roleLabel = user?.profile?.role === 'councillor' ? 'Councillor'
      : user?.profile?.role === 'admin' ? 'Admin' : 'Citizen';
    return (
      <div className="nav-auth">
        <Link to={user?.profile?.role === 'admin' ? '/admin-portal' : user?.profile?.role === 'councillor' ? '/councillor-portal' : '/dashboard'} className="nav-auth-user">
          <UserIcon size={16} />
          <span className="nav-auth-name">{user.username}</span>
          <span className="nav-auth-role">{roleLabel}</span>
        </Link>
        <button className="nav-auth-logout" onClick={() => { logout(); navigate('/'); }} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="nav-auth">
      <Link to="/login" className="nav-auth-btn">
        <LogIn size={15} /> Sign In
      </Link>
      <Link to="/signup" className="nav-auth-btn nav-auth-btn-primary">
        <UserPlus size={15} /> Sign Up
      </Link>
    </div>
  );
}

/* --- Landing Page --- */
function LandingPage() {
  const [selectedWard, setSelectedWard] = useState(null);
  const [showComplaintModal, setShowComplaintModal] = useState(false);
  const [whatsappConfig, setWhatsappConfig] = useState(null);
  const { isAuthenticated, user } = useAuth();

  React.useEffect(() => {
    fetch('/api/public/config/')
      .then(r => r.json())
      .then(setWhatsappConfig)
      .catch(() => {});
  }, []);

  return (
    <div className="landing-page">
      {/* --- Navbar --- */}
      <Navbar
        showReportBtn
        onReportClick={() => setShowComplaintModal(true)}
      />

      {/* ──────────────── HERO ──────────────── */}
      <section className="hero-section" id="hero">
        <div className="hero-glow hero-glow-1"></div>
        <div className="hero-glow hero-glow-2"></div>
        <div className="hero-content">
          <div className="hero-badge">Mumbai Urban Intelligence Platform</div>
          <h1 className="hero-title">
            Mumbai's infrastructure is <span className="hero-highlight">failing silently.</span>
            <br />We track it publicly.
          </h1>
          <p className="hero-subtitle">
            Every year, Mumbai's 24 wards generate over <strong>900,000 civic complaints</strong> —
            potholes, water leaks, garbage pile-ups, broken streetlights. Most sit unresolved for weeks.
            <strong> UrbanIQ</strong> maps every complaint, scores every ward, and holds every councillor
            accountable — all in one open platform.
          </p>
          <div className="hero-actions">
            <a href="#how-it-works" className="btn btn-primary">How to File a Complaint</a>
            <a href="#map-section" className="btn btn-ghost">Explore the Map</a>
            <Link to="/dashboard" className="btn btn-ghost" id="hero-dashboard-btn">
              Full Dashboard
            </Link>
          </div>
        </div>
        <div className="hero-scroll-hint">
          <span>Scroll to explore</span>
          <div className="scroll-arrow"><ArrowDown size={20} /></div>
        </div>
      </section>

      {/* ──────────────── THE PROBLEM ──────────────── */}
      <section className="stats-section" id="problem">
        <div className="section-header">
          <span className="section-tag">The Problem</span>
          <h2 className="section-title">The scale of Mumbai's civic crisis</h2>
          <p className="section-desc">
            Data from the Praja Foundation reveals a staggering gap between complaints filed and
            grievances resolved. These numbers represent millions of Mumbaikars waiting for basic services.
          </p>
        </div>
        <div className="stats-grid">
          <div className="stat-card stat-card-complaints">
            <div className="stat-number">9,44,000+</div>
            <div className="stat-label">Complaints filed every year</div>
            <div className="stat-sub">across all 24 administrative wards</div>
          </div>
          <div className="stat-card stat-card-warn">
            <div className="stat-number">42 days</div>
            <div className="stat-label">Average resolution time</div>
            <div className="stat-sub">some wards average over 68 days</div>
          </div>
          <div className="stat-card stat-card-danger">
            <div className="stat-number">13%</div>
            <div className="stat-label">Get escalated</div>
            <div className="stat-sub">unresolved at the first level of response</div>
          </div>
          <div className="stat-card stat-card-info">
            <div className="stat-number">24</div>
            <div className="stat-label">Wards, wildly unequal</div>
            <div className="stat-sub">some perform 3× better than others</div>
          </div>
          <div className="stat-card stat-card-budget">
            <div className="stat-number">46%</div>
            <div className="stat-label">Maintenance budget utilized</div>
            <div className="stat-sub">over 50% of civic funds go unspent each year</div>
          </div>
          <div className="stat-card stat-card-water">
            <div className="stat-number">1.2L+</div>
            <div className="stat-label">Water & sewer complaints</div>
            <div className="stat-sub">dirty water, leaks & drainage top the list</div>
          </div>
        </div>
      </section>

      {/* ──────────────── HOW IT WORKS ──────────────── */}
      <section className="steps-section" id="how-it-works">
        <div className="section-header">
          <span className="section-tag">How It Works</span>
          <h2 className="section-title">File a complaint in 4 simple steps</h2>
          <p className="section-desc">
            Whether you use the web form or WhatsApp, the process takes under 2 minutes.
            Your complaint is geo-tagged, assigned to the correct ward, and tracked until resolution.
          </p>
        </div>
        <div className="steps-grid">
          <div className="step-card">
            <div className="step-number">1</div>
            <div className="step-icon"><Megaphone size={24} color="#818cf8" /></div>
            <h3>Choose a Category</h3>
            <p>Pick the issue type — pothole, water leak, garbage, street light, drainage, road damage, or other.</p>
          </div>
          <div className="step-arrow"><span>→</span></div>
          <div className="step-card">
            <div className="step-number">2</div>
            <div className="step-icon"><Camera size={24} color="#818cf8" /></div>
            <h3>Describe &amp; Snap</h3>
            <p>Briefly describe the problem and upload a photo so authorities can assess the severity immediately.</p>
          </div>
          <div className="step-arrow"><span>→</span></div>
          <div className="step-card">
            <div className="step-number">3</div>
            <div className="step-icon"><MapPin size={24} color="#818cf8" /></div>
            <h3>Pin the Location</h3>
            <p>Share your location automatically or select your ward manually. The complaint lands on the right desk.</p>
          </div>
          <div className="step-arrow"><span>→</span></div>
          <div className="step-card">
            <div className="step-number">4</div>
            <div className="step-icon"><CheckCircle size={24} color="#818cf8" /></div>
            <h3>Track Until Done</h3>
            <p>Get a reference ID, track status any time, and see your complaint reflected on the public map.</p>
          </div>
        </div>
        <div className="steps-cta">
          <p>Two ways to file:</p>
          <div className="steps-cta-btns">
            <button className="btn btn-primary" onClick={() => setShowComplaintModal(true)}>
              <Megaphone size={16} /> Web Form
            </button>
            <a href="#file-whatsapp" className="btn btn-whatsapp">
              <MessageSquare size={16} /> WhatsApp
            </a>
          </div>
        </div>
      </section>

      {/* ──────────────── MAP SECTION ──────────────── */}
      <section className="map-section" id="map-section">
        <div className="section-header">
          <span className="section-tag">Live Intelligence</span>
          <h2 className="section-title">Ward-level infrastructure health, visualized</h2>
          <p className="section-desc">
            Each ward is colour-coded by its health score — a composite of complaint volume,
            resolution speed, and civic participation. Hover any ward for details.
            <strong> Red zones need urgent attention.</strong>
          </p>
        </div>
        <div className="map-container" id="interactive-map">
          <MumbaiMap onWardClick={setSelectedWard} />
        </div>
      </section>

      {/* ──────────────── FEATURES ──────────────── */}
      <section className="features-section" id="features">
        <div className="section-header">
          <span className="section-tag">Why UrbanIQ</span>
          <h2 className="section-title">Turning scattered complaints into urban intelligence</h2>
          <p className="section-desc">
            Our platform brings together data from multiple sources to give citizens, administrators,
            and councillors a single source of truth about Mumbai's civic infrastructure.
          </p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Map size={32} color="#818cf8" /></div>
            <h3>Geospatial Analytics</h3>
            <p>
              Every complaint is pinned to a precise location. Spot infrastructure failure clusters,
              identify underserved neighbourhoods, and allocate resources where they matter most.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><BarChart2 size={32} color="#818cf8" /></div>
            <h3>Ward Health Scores</h3>
            <p>
              A single, data-driven score for every ward — combining complaint burden, resolution speed,
              and civic engagement. Compare wards at a glance and track improvement over time.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Activity size={32} color="#818cf8" /></div>
            <h3>Real-time Trends <span className="ml-badge">ML</span></h3>
            <p>
              Monitor complaint volumes as they change. ML-powered early-warning indicators flag emerging hotspots
              before they become full-blown crises — giving administrators time to act.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><ShieldCheck size={32} color="#818cf8" /></div>
            <h3>Councillor Accountability</h3>
            <p>
              Every ward's performance is public. Compare councillors by deliberation activity,
              response rates, and resolution times. Data-driven accountability for elected representatives.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Crosshair size={32} color="#818cf8" /></div>
            <h3>Automated Ward Matching <span className="ml-badge">ML</span></h3>
            <p>
              AI-powered routing maps every complaint to the correct ward — even with partial or
              inconsistent input. No more complaints falling through administrative cracks.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Search size={32} color="#818cf8" /></div>
            <h3>Reference-Based Tracking</h3>
            <p>
              Every complaint gets a unique reference number. Citizens can track resolution status
              24×7 via the web portal or WhatsApp — no login required.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><TrendingUp size={32} color="#818cf8" /></div>
            <h3>AI Predictions &amp; Forecasts <span className="ml-badge">ML</span></h3>
            <p>
              ML models forecast complaint volumes, risk levels, and health scores for every ward 1–2
              years ahead. Councillors get early warnings and actionable recommendations before problems escalate.
            </p>
          </div>
        </div>
      </section>

      {/* ──────────────── FILE VIA WHATSAPP ──────────────── */}
      <section className="whatsapp-section" id="file-whatsapp">
        <div className="section-header">
          <span className="section-tag">File via WhatsApp</span>
          <h2 className="section-title">No app? No problem.</h2>
          <p className="section-desc">
            You don't need to sign up or install anything. Scan the QR code to open WhatsApp
            and file a complaint in under a minute. The bot guides you step by step.
          </p>
        </div>
        <div className="whatsapp-card">
          <div className="whatsapp-qr">
            {whatsappConfig?.whatsapp_link ? (
              <a href={whatsappConfig.whatsapp_link} target="_blank" rel="noopener noreferrer">
                <QRCodeSVG
                  value={whatsappConfig.whatsapp_link}
                  size={180}
                  bgColor="#ffffff"
                  fgColor="#075e54"
                  level="M"
                  style={{ borderRadius: 12 }}
                />
              </a>
            ) : (
              <div className="whatsapp-qr-placeholder">
                <Smartphone size={48} color="#25D366" />
              </div>
            )}
          </div>
          <div className="whatsapp-info">
            <div className="whatsapp-number">
              <Smartphone size={20} color="#25D366" />
              <span>{whatsappConfig?.whatsapp_number || 'Loading...'}</span>
            </div>
            <p className="whatsapp-desc">
              Scan the QR code with your phone camera, or tap the button below to open WhatsApp immediately.
              No login, no sign-up — just send a message and follow the bot.
            </p>
            <div className="whatsapp-steps">
              <div className="whatsapp-step">
                <span className="whatsapp-step-num">1</span>
                <span>Send the category — e.g. "Pothole"</span>
              </div>
              <div className="whatsapp-step">
                <span className="whatsapp-step-num">2</span>
                <span>Describe the problem</span>
              </div>
              <div className="whatsapp-step">
                <span className="whatsapp-step-num">3</span>
                <span>Share a photo (optional)</span>
              </div>
              <div className="whatsapp-step">
                <span className="whatsapp-step-num">4</span>
                <span>Send your location — done!</span>
              </div>
            </div>
            {whatsappConfig?.whatsapp_link ? (
              <a
                href={whatsappConfig.whatsapp_link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-whatsapp btn-whatsapp-lg"
              >
                <ExternalLink size={18} /> Open WhatsApp
              </a>
            ) : (
              <p style={{ color: '#64748b', fontSize: '0.82rem', marginTop: '1rem' }}>
                WhatsApp bot not yet configured. Contact your administrator to set up Twilio credentials.
              </p>
            )}
            {whatsappConfig && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.75rem' }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: whatsappConfig.twilio_configured ? '#22c55e' : '#ef4444',
                  flexShrink: 0,
                }} />
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  WhatsApp Bot {whatsappConfig.twilio_configured ? 'Active' : 'Disconnected'}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ──────────────── COUNCILLOR ACCOUNTABILITY ──────────────── */}
      <section className="accountability-section" id="accountability">
        <div className="section-header">
          <span className="section-tag">Councillor Accountability</span>
          <h2 className="section-title">Who is representing your ward?</h2>
          <p className="section-desc">
            Per-capita deliberations are a strong indicator of councillor engagement. Wards with
            higher deliberation counts tend to have faster resolution times.
            <strong> Sort the table to find your ward.</strong>
          </p>
        </div>
        <CouncillorTable />
      </section>

      {/* ──────────────── FOOTER ──────────────── */}
      <footer className="site-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <Hexagon className="nav-icon" size={20} />
            <span>UrbanIQ</span>
          </div>
          <p className="footer-text">
            Built for Mumbai. Powered by open civic data from the Praja Foundation.
          </p>
          <div className="footer-links">
            <a href="#hero">Home</a>
            <a href="#problem">The Problem</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#map-section">Live Map</a>
            <a href="#features">Features</a>
            <Link to="/complaints-map">Complaint Map</Link>
            <Link to="/dashboard">Dashboard</Link>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
            <Link to="/admin-portal" style={{ color: '#818cf8', textDecoration: 'none', fontSize: '0.875rem' }}>
              Admin Portal
            </Link>
            <Link to="/public" style={{ color: '#818cf8', textDecoration: 'none', fontSize: '0.875rem' }}>
              Public Dashboard
            </Link>
            <Link to="/complaints-map" style={{ color: '#818cf8', textDecoration: 'none', fontSize: '0.875rem' }}>
              Complaint Map
            </Link>
          </div>
        </div>
      </footer>

      {/* --- Ward Detail Panel --- */}
      <WardDetailPanel ward={selectedWard} onClose={() => setSelectedWard(null)} />

      {/* --- Complaint Modal --- */}
      {showComplaintModal && (
        <ComplaintModal onClose={() => setShowComplaintModal(false)} />
      )}
    </div>
  );
}

/* --- App with Router --- */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/track" element={<TrackComplaint />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/admin-portal" element={<AdminPortal />} />
          <Route path="/councillor-portal" element={<CouncillorPortal />} />
          <Route path="/public" element={<PublicDashboard />} />
          <Route path="/complaints-map" element={<ComplaintsMap />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
