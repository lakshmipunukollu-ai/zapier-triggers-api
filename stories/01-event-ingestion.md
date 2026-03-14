# Story 1: Event Ingestion

## As a developer, I want to ingest events into the Triggers API so they can be delivered to consumers.

### Acceptance Criteria
- POST /v1/events accepts source, event_type, and payload
- Returns event ID and status on success (201)
- Idempotency: duplicate events within 60s return existing ID (200)
- Idempotency key = SHA256(source + event_type + payload_json)
- Event is persisted to PostgreSQL with status "pending"
- Event ID is pushed to Redis queue for delivery processing
- Input validation via Pydantic models
- JWT authentication required

### Technical Notes
- Event ID format: "evt_" + 16 hex chars from uuid4
- Payload stored as JSONB in PostgreSQL
- Redis LPUSH to "events:pending" queue on ingestion
