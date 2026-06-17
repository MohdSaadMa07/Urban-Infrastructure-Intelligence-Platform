import React from 'react';
import MumbaiMap from './components/MumbaiMap';
import './App.css';

function App() {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Mumbai Urban Intelligence Platform</h1>
        <p>Ward-level geospatial analytics and predictive maintenance</p>
      </header>
      <main className="dashboard-main">
        <div className="map-container">
          <MumbaiMap />
        </div>
      </main>
    </div>
  );
}

export default App;
