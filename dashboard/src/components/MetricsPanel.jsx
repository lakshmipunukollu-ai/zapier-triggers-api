import React, { useState, useEffect } from 'react';
import { fetchMetrics } from '../api/client';

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await fetchMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) return <p>Loading metrics...</p>;
  if (error) return <p style={{ color: '#e53e3e' }}>Error: {error}</p>;
  if (!metrics) return null;

  const cards = [
    { label: 'Total Events', value: metrics.total_events, color: '#2b6cb0' },
    { label: 'Pending', value: metrics.pending, color: '#d69e2e' },
    { label: 'Delivered', value: metrics.delivered, color: '#38a169' },
    { label: 'Acked', value: metrics.acked, color: '#319795' },
    { label: 'Failed', value: metrics.failed, color: '#e53e3e' },
    { label: 'Dead Letter', value: metrics.dead, color: '#9b2c2c' },
  ];

  return (
    <div>
      <div style={styles.grid}>
        {cards.map((card) => (
          <div key={card.label} style={{ ...styles.card, borderTop: `4px solid ${card.color}` }}>
            <div style={styles.cardLabel}>{card.label}</div>
            <div style={{ ...styles.cardValue, color: card.color }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={styles.latencyCard}>
        <div style={styles.cardLabel}>Avg Delivery Time</div>
        <div style={styles.cardValue}>{metrics.avg_delivery_time_ms.toFixed(1)} ms</div>
      </div>

      <button onClick={load} style={styles.refresh}>Refresh</button>
    </div>
  );
}

const styles = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: 16,
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 20,
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  cardLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  cardValue: {
    fontSize: 32,
    fontWeight: 700,
    marginTop: 8,
  },
  latencyCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 20,
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderTop: '4px solid #805ad5',
    display: 'inline-block',
    minWidth: 200,
  },
  refresh: {
    marginTop: 16,
    padding: '8px 20px',
    border: 'none',
    borderRadius: 6,
    backgroundColor: '#ff4a00',
    color: '#fff',
    cursor: 'pointer',
    fontWeight: 600,
    marginLeft: 16,
  },
};
