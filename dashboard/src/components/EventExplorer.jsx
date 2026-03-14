import React, { useState, useEffect } from 'react';
import { fetchEvents, fetchEventStatus, ackEvent, deleteEvent, createEvent } from '../api/client';
import EventDetail from './EventDetail';

export default function EventExplorer() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [filters, setFilters] = useState({ source: '', event_type: '', limit: '10' });
  const [showCreate, setShowCreate] = useState(false);
  const [newEvent, setNewEvent] = useState({ source: '', event_type: '', payload: '{}' });

  const load = async () => {
    try {
      setLoading(true);
      const data = await fetchEvents({
        consumer_id: 'dashboard',
        source: filters.source || undefined,
        event_type: filters.event_type || undefined,
        limit: filters.limit || '10',
      });
      setEvents(data.events || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleViewStatus = async (eventId) => {
    try {
      const data = await fetchEventStatus(eventId);
      setSelectedEvent(data);
    } catch (err) {
      alert('Error loading event status: ' + err.message);
    }
  };

  const handleAck = async (eventId) => {
    try {
      await ackEvent(eventId, 'dashboard');
      load();
    } catch (err) {
      alert('Error acknowledging: ' + err.message);
    }
  };

  const handleDelete = async (eventId) => {
    if (!confirm('Delete this event?')) return;
    try {
      await deleteEvent(eventId);
      load();
    } catch (err) {
      alert('Error deleting: ' + err.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      let payload;
      try {
        payload = JSON.parse(newEvent.payload);
      } catch {
        alert('Invalid JSON payload');
        return;
      }
      await createEvent({
        source: newEvent.source,
        event_type: newEvent.event_type,
        payload,
      });
      setShowCreate(false);
      setNewEvent({ source: '', event_type: '', payload: '{}' });
      load();
    } catch (err) {
      alert('Error creating event: ' + err.message);
    }
  };

  if (selectedEvent) {
    return <EventDetail event={selectedEvent} onBack={() => setSelectedEvent(null)} />;
  }

  return (
    <div>
      <div style={styles.toolbar}>
        <h2 style={styles.heading}>Event Explorer</h2>
        <button onClick={() => setShowCreate(!showCreate)} style={styles.createBtn}>
          {showCreate ? 'Cancel' : '+ New Event'}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} style={styles.form}>
          <input
            placeholder="Source (e.g. github.com)"
            value={newEvent.source}
            onChange={(e) => setNewEvent({ ...newEvent, source: e.target.value })}
            style={styles.input}
            required
          />
          <input
            placeholder="Event Type (e.g. push)"
            value={newEvent.event_type}
            onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
            style={styles.input}
            required
          />
          <textarea
            placeholder='Payload JSON (e.g. {"key": "value"})'
            value={newEvent.payload}
            onChange={(e) => setNewEvent({ ...newEvent, payload: e.target.value })}
            style={{ ...styles.input, minHeight: 60 }}
          />
          <button type="submit" style={styles.submitBtn}>Create Event</button>
        </form>
      )}

      <div style={styles.filters}>
        <input
          placeholder="Filter by source"
          value={filters.source}
          onChange={(e) => setFilters({ ...filters, source: e.target.value })}
          style={styles.filterInput}
        />
        <input
          placeholder="Filter by event_type"
          value={filters.event_type}
          onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
          style={styles.filterInput}
        />
        <select
          value={filters.limit}
          onChange={(e) => setFilters({ ...filters, limit: e.target.value })}
          style={styles.filterInput}
        >
          <option value="10">10</option>
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
        <button onClick={load} style={styles.filterBtn}>Search</button>
      </div>

      {loading && <p>Loading events...</p>}
      {error && <p style={{ color: '#e53e3e' }}>Error: {error}</p>}

      {!loading && events.length === 0 && <p style={styles.empty}>No pending events found.</p>}

      {events.length > 0 && (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Source</th>
              <th style={styles.th}>Type</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Attempts</th>
              <th style={styles.th}>Created</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {events.map((evt) => (
              <tr key={evt.id} style={styles.tr}>
                <td style={styles.td}>
                  <code style={styles.code}>{evt.id}</code>
                </td>
                <td style={styles.td}>{evt.source}</td>
                <td style={styles.td}>{evt.event_type}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, ...statusColor(evt.delivery_status) }}>
                    {evt.delivery_status}
                  </span>
                </td>
                <td style={styles.td}>{evt.delivery_attempts}</td>
                <td style={styles.td}>{new Date(evt.created_at).toLocaleString()}</td>
                <td style={styles.td}>
                  <button onClick={() => handleViewStatus(evt.id)} style={styles.actionBtn}>Status</button>
                  <button onClick={() => handleAck(evt.id)} style={styles.actionBtn}>Ack</button>
                  <button onClick={() => handleDelete(evt.id)} style={{ ...styles.actionBtn, color: '#e53e3e' }}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function statusColor(status) {
  const map = {
    pending: { backgroundColor: '#fefcbf', color: '#744210' },
    delivered: { backgroundColor: '#c6f6d5', color: '#22543d' },
    acked: { backgroundColor: '#b2f5ea', color: '#234e52' },
    failed: { backgroundColor: '#fed7d7', color: '#742a2a' },
    dead: { backgroundColor: '#e2e8f0', color: '#4a5568' },
  };
  return map[status] || {};
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
  input: {
    padding: '8px 12px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14,
  },
  submitBtn: {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    backgroundColor: '#38a169', color: '#fff', cursor: 'pointer', fontWeight: 600, alignSelf: 'flex-start',
  },
  filters: { display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' },
  filterInput: {
    padding: '8px 12px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14, minWidth: 150,
  },
  filterBtn: {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    backgroundColor: '#2b6cb0', color: '#fff', cursor: 'pointer', fontWeight: 600,
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
    backgroundColor: '#fff', cursor: 'pointer', fontSize: 12, marginRight: 4, color: '#2b6cb0',
  },
};
