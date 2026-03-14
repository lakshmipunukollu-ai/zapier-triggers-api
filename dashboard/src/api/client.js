const API_BASE = '/v1';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }
  return res.json();
}

export async function fetchMetrics() {
  return request('/metrics');
}

export async function fetchEvents(params = {}) {
  const qs = new URLSearchParams();
  qs.set('consumer_id', params.consumer_id || 'dashboard');
  if (params.event_type) qs.set('event_type', params.event_type);
  if (params.source) qs.set('source', params.source);
  if (params.limit) qs.set('limit', params.limit);
  return request(`/inbox?${qs.toString()}`);
}

export async function fetchEventStatus(eventId) {
  return request(`/events/${eventId}/status`);
}

export async function createEvent(data) {
  return request('/events', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function ackEvent(eventId, consumerId) {
  return request(`/events/${eventId}/ack`, {
    method: 'POST',
    body: JSON.stringify({ consumer_id: consumerId }),
  });
}

export async function deleteEvent(eventId) {
  return request(`/events/${eventId}`, {
    method: 'DELETE',
  });
}

export async function fetchSubscriptions(consumerId) {
  const qs = consumerId ? `?consumer_id=${consumerId}` : '';
  return request(`/subscriptions${qs}`);
}

export async function createSubscription(data) {
  return request('/subscriptions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteSubscription(subId) {
  return request(`/subscriptions/${subId}`, {
    method: 'DELETE',
  });
}

export async function fetchHealth() {
  const res = await fetch('/health');
  return res.json();
}
