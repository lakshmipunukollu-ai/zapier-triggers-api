# Zapier Triggers API — Architecture Document

## Overview

The Triggers API is a platform primitive for Zapier that enables event ingestion, reliable delivery, and consumption. It provides both push (webhook) and pull (inbox polling) delivery mechanisms with at-least-once delivery guarantees.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                  │
│                                                          │
│  POST /v1/events          — Ingest events                │
│  GET  /v1/inbox           — Pull undelivered events      │
│  POST /v1/events/:id/ack  — Acknowledge consumption      │
│  DELETE /v1/events/:id    — Delete after consumption     │
│  POST /v1/subscriptions   — Subscribe to event types     │
│  GET  /v1/events/:id/status — Delivery status + history  │
│  GET  /v1/metrics         — Event counts & latency       │
│  GET  /health             — Health check                 │
└───────────┬─────────────────────────┬────────────────────┘
            │                         │
     ┌──────▼──────┐          ┌───────▼───────┐
     │  PostgreSQL  │          │     Redis      │
     │  (persistent │          │  (event queue, │
     │   storage)   │          │   locks, cache)│
     └──────┬──────┘          └───────┬───────┘
            │                         │
     ┌──────▼─────────────────────────▼───────┐
     │         Delivery Worker (Background)     │
     │                                          │
     │  PushDelivery — webhook POST to URLs     │
     │  RetryScheduler — exponential backoff    │
     │  DeadLetterHandler — after 7 failures    │
     └──────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI (Python 3.11+) | Auto OpenAPI docs, async support, DX-first |
| ORM | SQLAlchemy 1.4 (sync session.query style) | Mature, well-supported |
| Database | PostgreSQL | ACID, JSON support for payloads |
| Queue/Cache | Redis | Event queue durability, locking, pub/sub |
| Task Worker | Background threads (asyncio) | Simpler than Celery for v1 |
| Auth | JWT (python-jose + passlib) | Stateless, scalable |

## Data Models

### Event (Core)
```
events
├── id              VARCHAR(24) PK    — "evt_" + 16 hex chars
├── source          VARCHAR(255)       — e.g. "github.com", "stripe"
├── event_type      VARCHAR(255)       — e.g. "push", "payment.succeeded"
├── payload         JSONB              — arbitrary event data
├── idempotency_key VARCHAR(64) UNIQUE — SHA256(source + event_type + payload)
├── delivery_status VARCHAR(20)        — pending/delivered/acked/failed/dead
├── delivery_attempts INT DEFAULT 0
├── consumer_id     VARCHAR(255) NULL
├── locked_until    TIMESTAMP NULL     — visibility timeout lock
├── last_attempt_at TIMESTAMP NULL
├── acked_at        TIMESTAMP NULL
├── created_at      TIMESTAMP
├── updated_at      TIMESTAMP
```

### Subscription
```
subscriptions
├── id              VARCHAR(24) PK    — "sub_" + 16 hex chars
├── consumer_id     VARCHAR(255)
├── event_type      VARCHAR(255) NULL  — filter by type (NULL = all)
├── source          VARCHAR(255) NULL  — filter by source (NULL = all)
├── webhook_url     VARCHAR(2048) NULL — for push delivery
├── is_active       BOOLEAN DEFAULT TRUE
├── created_at      TIMESTAMP
├── updated_at      TIMESTAMP
```

### DeliveryLog
```
delivery_logs
├── id              SERIAL PK
├── event_id        VARCHAR(24) FK
├── attempt_number  INT
├── status_code     INT NULL           — HTTP status from webhook
├── response_body   TEXT NULL
├── error_message   TEXT NULL
├── attempted_at    TIMESTAMP
├── duration_ms     INT NULL
```

## API Contracts

### POST /v1/events — Ingest Event
```json
// Request
{
  "source": "github.com",
  "event_type": "push",
  "payload": { "repo": "zapier/triggers", "branch": "main" }
}

// Response 201
{
  "id": "evt_a1b2c3d4e5f67890",
  "source": "github.com",
  "event_type": "push",
  "delivery_status": "pending",
  "created_at": "2026-03-14T00:00:00Z"
}

// Duplicate within 60s → 200 with existing event
```

### GET /v1/inbox — Pull Events
```
Query params: consumer_id (required), event_type, source, limit (default 10, max 100)

// Response 200
{
  "events": [...],
  "count": 3
}
```

Events are locked (visibility timeout 30s) upon retrieval. Consumer must ACK within 30s or event becomes available again.

### POST /v1/events/:id/ack — Acknowledge Event
```json
// Request
{ "consumer_id": "my-service-01" }

// Response 200
{ "id": "evt_...", "delivery_status": "acked", "acked_at": "..." }
```

### DELETE /v1/events/:id — Delete Event
```json
// Response 200
{ "deleted": true, "id": "evt_..." }
```

### POST /v1/subscriptions — Create Subscription
```json
// Request
{
  "consumer_id": "my-service-01",
  "event_type": "push",
  "source": "github.com",
  "webhook_url": "https://my-service.com/webhook"
}

// Response 201
{ "id": "sub_...", "consumer_id": "...", ... }
```

### GET /v1/events/:id/status — Event Status
```json
// Response 200
{
  "id": "evt_...",
  "delivery_status": "delivered",
  "delivery_attempts": 2,
  "delivery_log": [
    { "attempt": 1, "status_code": 500, "error": "...", "at": "..." },
    { "attempt": 2, "status_code": 200, "at": "..." }
  ]
}
```

### GET /v1/metrics — System Metrics
```json
// Response 200
{
  "total_events": 15234,
  "pending": 42,
  "delivered": 14800,
  "failed": 12,
  "dead": 3,
  "avg_delivery_time_ms": 145
}
```

### GET /health — Health Check
```json
// Response 200
{ "status": "healthy", "database": "connected", "redis": "connected" }
```

## Reliability Design

### Delivery Guarantee: At-Least-Once

**Why not exactly-once:** Exactly-once requires distributed transactions (2PC) across the event store and delivery record. This adds significant latency and operational complexity. At-least-once is achievable with an idempotency key (event.id) that consumers can use to deduplicate on their end. This mirrors how Stripe webhooks and AWS SQS work.

### Idempotency

POST /v1/events is idempotent on `SHA256(source + event_type + JSON(payload))`. Duplicate submissions within a 60-second window return the existing event ID with a 200 status.

### Retry Policy

Exponential backoff: 1s, 5s, 30s, 5min, 30min, 2hr, 8hr (7 attempts). After 7 failures, event moves to dead-letter queue (status = "dead") for manual inspection.

### Visibility Timeout (Lock Pattern)

When /inbox returns events, they are soft-locked for 30 seconds via Redis. This prevents double-delivery to multiple consumers polling simultaneously. If consumer does not ACK within 30s, the lock expires and the event becomes available again. This mirrors the AWS SQS visibility timeout pattern.

### Dead Letter Queue

Events that exhaust all retry attempts (7) are moved to "dead" status. They remain in the database for inspection via GET /v1/events/:id/status and can be manually requeued.

## Security

- All API endpoints require JWT authentication (Bearer token)
- API keys are hashed with bcrypt before storage
- All secrets loaded from environment variables (.env file)
- Input validation on all endpoints via Pydantic models
- Rate limiting: 1000 requests/minute per consumer

## Deviations from Brief

1. **Background threads instead of Celery**: For v1, using asyncio background tasks instead of a separate Celery worker process. This simplifies deployment while maintaining the same retry semantics. Can be upgraded to Celery in v2 if needed.

2. **SQLAlchemy 1.4 sync style**: Using `session.query(Model)` pattern as specified, not the 2.0 `select()` style shown in the brief's inbox example code.

3. **JWT Auth**: Added JWT authentication to all endpoints for security, even though the brief doesn't explicitly require it. API keys are generated per consumer.
