import React from 'react';

export default function EventDetail({ event, onBack }) {
  return (
    <div>
      <button onClick={onBack} style={styles.back}>Back to Events</button>

      <div style={styles.card}>
        <h2 style={styles.heading}>Event Detail</h2>

        <div style={styles.grid}>
          <div style={styles.field}>
            <label style={styles.label}>Event ID</label>
            <code style={styles.value}>{event.id}</code>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Source</label>
            <span style={styles.value}>{event.source}</span>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Event Type</label>
            <span style={styles.value}>{event.event_type}</span>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Status</label>
            <span style={styles.value}>{event.delivery_status}</span>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Delivery Attempts</label>
            <span style={styles.value}>{event.delivery_attempts}</span>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Created At</label>
            <span style={styles.value}>
              {event.created_at ? new Date(event.created_at).toLocaleString() : 'N/A'}
            </span>
          </div>
          {event.acked_at && (
            <div style={styles.field}>
              <label style={styles.label}>Acked At</label>
              <span style={styles.value}>{new Date(event.acked_at).toLocaleString()}</span>
            </div>
          )}
          {event.last_attempt_at && (
            <div style={styles.field}>
              <label style={styles.label}>Last Attempt</label>
              <span style={styles.value}>{new Date(event.last_attempt_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {event.delivery_log && event.delivery_log.length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.subHeading}>Delivery Log</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Attempt</th>
                <th style={styles.th}>Status Code</th>
                <th style={styles.th}>Duration (ms)</th>
                <th style={styles.th}>Error</th>
                <th style={styles.th}>Time</th>
              </tr>
            </thead>
            <tbody>
              {event.delivery_log.map((log, i) => (
                <tr key={i} style={styles.tr}>
                  <td style={styles.td}>{log.attempt}</td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.statusBadge,
                      backgroundColor: log.status_code && log.status_code < 300 ? '#c6f6d5' : '#fed7d7',
                    }}>
                      {log.status_code || 'N/A'}
                    </span>
                  </td>
                  <td style={styles.td}>{log.duration_ms != null ? `${log.duration_ms}ms` : 'N/A'}</td>
                  <td style={styles.td}>{log.error || '-'}</td>
                  <td style={styles.td}>{new Date(log.at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(!event.delivery_log || event.delivery_log.length === 0) && (
        <div style={styles.card}>
          <p style={{ color: '#718096' }}>No delivery attempts recorded.</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  back: {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    backgroundColor: '#e2e8f0', cursor: 'pointer', fontWeight: 600, marginBottom: 16,
  },
  card: {
    backgroundColor: '#fff', borderRadius: 8, padding: 24, marginBottom: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  heading: { fontSize: 20, fontWeight: 700, margin: '0 0 16px 0' },
  subHeading: { fontSize: 16, fontWeight: 700, margin: '0 0 12px 0' },
  grid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16,
  },
  field: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 12, fontWeight: 600, color: '#718096', textTransform: 'uppercase' },
  value: { fontSize: 14, fontWeight: 500 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { padding: '10px 12px', textAlign: 'left', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#4a5568', backgroundColor: '#edf2f7' },
  tr: { borderBottom: '1px solid #edf2f7' },
  td: { padding: '8px 12px', fontSize: 14 },
  statusBadge: { padding: '2px 8px', borderRadius: 8, fontSize: 12, fontWeight: 600 },
};
