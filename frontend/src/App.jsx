import React from 'react';
import MumbaiMap from './components/MumbaiMap';
import './App.css';

function App() {
  return (
    <div className="landing-page">
      {/* ─── Navbar ─── */}
      <nav className="navbar" id="navbar">
        <div className="nav-brand">
          <span className="nav-icon">◈</span>
          <span className="nav-title">UrbanIQ</span>
        </div>
        <div className="nav-links">
          <a href="#hero">Home</a>
          <a href="#problem">The Problem</a>
          <a href="#map-section">Live Map</a>
          <a href="#features">Features</a>
        </div>
      </nav>

      {/* ─── Hero Section ─── */}
      <section className="hero-section" id="hero">
        <div className="hero-glow hero-glow-1"></div>
        <div className="hero-glow hero-glow-2"></div>
        <div className="hero-content">
          <div className="hero-badge">Mumbai Urban Intelligence Platform</div>
          <h1 className="hero-title">
            Civic infrastructure is <span className="hero-highlight">failing silently.</span>
            <br />We make it visible.
          </h1>
          <p className="hero-subtitle">
            Every year, Mumbai's 24 wards generate over <strong>900,000 civic complaints</strong> — 
            potholes, water leaks, garbage overflow, drainage failures. Most go unresolved for weeks.
            Our platform turns this chaos into actionable, ward-level intelligence.
          </p>
          <div className="hero-actions">
            <a href="#map-section" className="btn btn-primary">Explore the Map</a>
            <a href="#problem" className="btn btn-ghost">See the Data</a>
          </div>
        </div>
        <div className="hero-scroll-hint">
          <span>Scroll to explore</span>
          <div className="scroll-arrow">↓</div>
        </div>
      </section>

      {/* ─── Problem / Stats Section ─── */}
      <section className="stats-section" id="problem">
        <div className="section-header">
          <span className="section-tag">The Problem</span>
          <h2 className="section-title">Mumbai's civic complaint crisis in numbers</h2>
          <p className="section-desc">
            Data from the Praja Foundation's annual report reveals a staggering scale of unresolved 
            infrastructure issues across the city. These numbers represent real people waiting for basic services.
          </p>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">9,44,000+</div>
            <div className="stat-label">Total complaints filed</div>
            <div className="stat-sub">across all 24 wards annually</div>
          </div>
          <div className="stat-card stat-card-warn">
            <div className="stat-number">42 days</div>
            <div className="stat-label">Average resolution time</div>
            <div className="stat-sub">some wards take over 68 days</div>
          </div>
          <div className="stat-card stat-card-danger">
            <div className="stat-number">13%</div>
            <div className="stat-label">Complaints escalated</div>
            <div className="stat-sub">unresolved at the first level</div>
          </div>
          <div className="stat-card stat-card-info">
            <div className="stat-number">24</div>
            <div className="stat-label">Administrative wards</div>
            <div className="stat-sub">with vastly different performance</div>
          </div>
        </div>
      </section>

      {/* ─── Map Section ─── */}
      <section className="map-section" id="map-section">
        <div className="section-header">
          <span className="section-tag">Live Intelligence</span>
          <h2 className="section-title">Ward-level infrastructure health, visualized</h2>
          <p className="section-desc">
            Each ward is color-coded by its infrastructure health score — combining complaint burden, 
            resolution speed, and civic engagement. Hover over any ward to see detailed metrics.
            <strong> Red zones need urgent attention.</strong>
          </p>
        </div>
        <div className="map-container" id="interactive-map">
          <MumbaiMap />
        </div>
      </section>

      {/* ─── Features / How It Helps Section ─── */}
      <section className="features-section" id="features">
        <div className="section-header">
          <span className="section-tag">Why UrbanIQ</span>
          <h2 className="section-title">From raw complaints to urban intelligence</h2>
          <p className="section-desc">
            Our platform transforms scattered civic data into a unified decision-support system 
            for administrators, councillors, and citizens.
          </p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🗺️</div>
            <h3>Geospatial Analytics</h3>
            <p>
              Pinpoint infrastructure failures at the ward level. See which neighborhoods 
              are underserved and where resources should be redirected.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Health Scoring</h3>
            <p>
              A composite score for each ward based on complaint volume, resolution speed, 
              and civic participation — making performance comparison instant.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Real-time Monitoring</h3>
            <p>
              Track complaint trends as they evolve. Identify emerging hotspots before 
              they become crises with early-warning indicators.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🏛️</div>
            <h3>Accountability Engine</h3>
            <p>
              Compare ward-level councillor activity, deliberation counts, and response 
              rates. Hold elected representatives accountable with data.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="site-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="nav-icon">◈</span>
            <span>UrbanIQ</span>
          </div>
          <p className="footer-text">
            Built for Mumbai. Powered by open civic data from the Praja Foundation.
          </p>
          <div className="footer-links">
            <a href="#hero">Home</a>
            <a href="#problem">The Problem</a>
            <a href="#map-section">Live Map</a>
            <a href="#features">Features</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
