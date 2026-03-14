import React, { useState, useEffect } from 'react';
import { fetchHealth } from '../api/client';

export default function HealthStatus() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchHealth();
        setHealth(data);
      } catch {
        setHealth({ status: 'unreachable', database: 'unknown', redis: 'unknown' });
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const color = health.status === 'healthy' ? '#38a169' : '#e53e3e';

  return (
    <div style={styles.container}>
      <span style={{ ...styles.dot, backgroundColor: color }} />
      <span style={styles.text}>
        API: {health.status} | DB: {health.database} | Redis: {health.redis}
      </span>
    </div>
  );
}

const styles = {
  container: { display: 'flex', alignItems: 'center', gap: 8 },
  dot: { width: 10, height: 10, borderRadius: '50%', display: 'inline-block' },
  text: { fontSize: 12, color: '#718096', fontWeight: 500 },
};
