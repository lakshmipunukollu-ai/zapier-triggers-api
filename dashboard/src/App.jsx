import React, { useState } from 'react';
import MetricsPanel from './components/MetricsPanel';
import EventExplorer from './components/EventExplorer';
import SubscriptionManager from './components/SubscriptionManager';
import HealthStatus from './components/HealthStatus';

const TABS = ['Metrics', 'Events', 'Subscriptions'];

export default function App() {
  const [activeTab, setActiveTab] = useState('Metrics');

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>Zapier Triggers Dashboard</h1>
        <HealthStatus />
      </header>

      <nav style={styles.nav}>
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              ...styles.tab,
              ...(activeTab === tab ? styles.activeTab : {}),
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      <main style={styles.main}>
        {activeTab === 'Metrics' && <MetricsPanel />}
        {activeTab === 'Events' && <EventExplorer />}
        {activeTab === 'Subscriptions' && <SubscriptionManager />}
      </main>
    </div>
  );
}

const styles = {
  app: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    maxWidth: 1200,
    margin: '0 auto',
    padding: '0 20px',
    color: '#1a1a2e',
    backgroundColor: '#f8f9fa',
    minHeight: '100vh',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 0',
    borderBottom: '2px solid #e2e8f0',
  },
  title: {
    fontSize: 24,
    fontWeight: 700,
    color: '#ff4a00',
    margin: 0,
  },
  nav: {
    display: 'flex',
    gap: 4,
    padding: '16px 0',
  },
  tab: {
    padding: '10px 24px',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 600,
    backgroundColor: '#e2e8f0',
    color: '#4a5568',
    transition: 'all 0.2s',
  },
  activeTab: {
    backgroundColor: '#ff4a00',
    color: '#fff',
  },
  main: {
    padding: '20px 0',
  },
};
