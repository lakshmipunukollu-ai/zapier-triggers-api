# Story 6: Event Status & System Metrics

## As a developer, I want to check event delivery status and view system metrics.

### Acceptance Criteria
- GET /v1/events/:id/status returns full delivery status + attempt history
- Includes delivery_log with each attempt's status_code, error, timestamp
- GET /v1/metrics returns aggregate statistics
- Metrics: total_events, pending, delivered, failed, dead, avg_delivery_time_ms
- JWT authentication required

### Technical Notes
- Metrics can be cached in Redis with 10s TTL for performance
- Delivery log joined from delivery_logs table
