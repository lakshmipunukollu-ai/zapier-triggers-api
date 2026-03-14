# Zapier Triggers API

A platform primitive for event ingestion, reliable delivery, and consumption. Supports both push (webhook) and pull (inbox polling) delivery with at-least-once guarantees.

## Architecture

- **API Layer**: FastAPI with JWT authentication
- **Database**: PostgreSQL (SQLAlchemy 1.4 ORM)
- **Queue/Cache**: Redis for event queue, locking, and visibility timeout
- **Delivery Worker**: Background async tasks with exponential backoff retry
- **Frontend**: React dashboard (Vite) for monitoring

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your database and Redis credentials

# Seed sample data
make seed

# Start the API server (port 3004)
make dev

# Run tests
make test

# Build frontend
cd dashboard && npm install && npm run build
```

## Ports

| Service   | Port |
|-----------|------|
| API       | 3004 |
| Frontend  | 5004 |
| Database  | PostgreSQL (zapier_triggers) |
| Redis     | 6380 |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST   | /v1/events | Ingest a new event |
| GET    | /v1/inbox | Pull pending events (visibility timeout lock) |
| POST   | /v1/events/:id/ack | Acknowledge event consumption |
| DELETE | /v1/events/:id | Delete an event |
| GET    | /v1/events/:id/status | Event delivery status + history |
| POST   | /v1/subscriptions | Create a subscription |
| GET    | /v1/subscriptions | List subscriptions |
| DELETE | /v1/subscriptions/:id | Delete a subscription |
| GET    | /v1/metrics | System metrics |
| GET    | /health | Health check |
| POST   | /auth/token | Generate JWT token |

## Reliability

- **At-least-once delivery** with idempotency keys (SHA256)
- **Exponential backoff retry**: 1s, 5s, 30s, 5min, 30min, 2hr, 8hr (7 attempts)
- **Dead letter queue**: Events exhausting retries are marked "dead" for inspection
- **Visibility timeout**: 30s SQS-style lock on inbox polling

## Testing

45 tests covering all endpoints, services, auth, and edge cases:

```bash
make test
```
