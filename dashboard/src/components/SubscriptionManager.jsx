import React, { useState, useEffect } from 'react';
import { fetchSubscriptions, createSubscription, deleteSubscription } from '../api/client';

export default function SubscriptionManager() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newSub, setNewSub] = useState({
    consumer_id: '', event_type: '', source: '', webhook_url: '',
  });

  const load = async () => {
    try {
      setLoading(true);
      const data = await fetchSubscriptions();
      setSubscriptions(data.subscriptions || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createSubscription({
        consumer_id: newSub.consumer_id,
        event_type: newSub.event_type || null,
        source: newSub.source || null,
        webhook_url: newSub.webhook_url || null,
      });
      setShowCreate(false);
      setNewSub({ consumer_id: '', event_type: '', source: '', webhook_url: '' });
      load();
    } catch (err) {
      alert('Error creating subscription: ' + err.message);
    }
  };

  const handleDelete = async (subId) => {
    if (!confirm('Delete this subscription?')) return;
    try {
      await deleteSubscription(subId);
      load();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <div>
      <div style={styles.toolbar}>
        <h2 style={styles.heading}>Subscriptions</h2>
        <button onClick={() => setShowCreate(!showCreate)} style={styles.createBtn}>
          {showCreate ? 'Cancel' : '+ New Subscription'}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} style={styles.form}>
          <input
            placeholder="Consumer ID (required)"
            value={newSub.consumer_id}
            onChange={(e) => setNewSub({ ...newSub, consumer_id: e.target.value })}
            style={styles.input}
            required
          />
          <input
            placeholder="Event Type (optional)"
            value={newSub.event_type}
            onChange={(e) => setNewSub({ ...newSub, event_type: e.target.value })}
            style={styles.input}
          />
          <input
            placeholder="Source (optional)"
            value={newSub.source}
            onChange={(e) => setNewSub({ ...newSub, source: e.target.value })}
            style={styles.input}
          />
          <input
            placeholder="Webhook URL (optional)"
            value={newSub.webhook_url}
            onChange={(e) => setNewSub({ ...newSub, webhook_url: e.target.value })}
            style={styles.input}
          />
          <button type="submit" style={styles.submitBtn}>Create Subscription</button>
        </form>
      )}

      {loading && <p>Loading subscriptions...</p>}
      {error && <p style={{ color: '#e53e3e' }}>Error: {error}</p>}

      {!loading && subscriptions.length === 0 && (
        <p style={styles.empty}>No subscriptions found.</p>
      )}

      {subscriptions.length > 0 && (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Consumer</th>
              <th style={styles.th}>Event Type</th>
              <th style={styles.th}>Source</th>
              <th style={styles.th}>Webhook URL</th>
              <th style={styles.th}>Active</th>
              <th style={styles.th}>Created</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.map((sub) => (
              <tr key={sub.id} style={styles.tr}>
                <td style={styles.td}><code style={styles.code}>{sub.id}</code></td>
                <td style={styles.td}>{sub.consumer_id}</td>
                <td style={styles.td}>{sub.event_type || '*'}</td>
                <td style={styles.td}>{sub.source || '*'}</td>
                <td style={styles.td}>{sub.webhook_url || '-'}</td>
                <td style={styles.td}>
                  <span style={{
                    ...styles.badge,
                    backgroundColor: sub.is_active ? '#c6f6d5' : '#fed7d7',
                    color: sub.is_active ? '#22543d' : '#742a2a',
                  }}>
                    {sub.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={styles.td}>{new Date(sub.created_at).toLocaleString()}</td>
                <td style={styles.td}>
                  <button
                    onClick={() => handleDelete(sub.id)}
                    style={{ ...styles.actionBtn, color: '#e53e3e' }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const styles = {
  toolbar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  heading: { fontSize: 20, fontWeight: 700, margin: 0 },
  createBtn: {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    backgroundColor: '#ff4a00', color: '#fff', cursor: 'pointer', fontWeight: 600,
  },
  form: {
    backgroundColor: '#fff', padding: 20, borderRadius: 8, marginBottom: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', gap: 10,
  },
  input: { padding: '8px 12px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14 },
  submitBtn: {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    backgroundColor: '#38a169', color: '#fff', cursor: 'pointer', fontWeight: 600, alignSelf: 'flex-start',
  },
  empty: { color: '#718096', fontStyle: 'italic' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  th: { padding: '12px 16px', textAlign: 'left', backgroundColor: '#edf2f7', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#4a5568' },
  tr: { borderBottom: '1px solid #edf2f7' },
  td: { padding: '10px 16px', fontSize: 14 },
  code: { fontSize: 12, backgroundColor: '#edf2f7', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' },
  badge: { padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 },
  actionBtn: {
    padding: '4px 10px', border: '1px solid #e2e8f0', borderRadius: 4,
    backgroundColor: '#fff', cursor: 'pointer', fontSize: 12,
  },
};
