# Build Summary — Zapier Triggers API

## Project Overview

Event ingestion and reliable delivery platform for Zapier. Supports push (webhook) and pull (inbox polling) delivery with at-least-once guarantees.

## What Was Built

### Backend (FastAPI + SQLAlchemy + Redis + PostgreSQL)

- **Event ingestion** with SHA256 idempotency keys and 60s dedup window
- **Inbox polling** with SQS-style 30s visibility timeout locking
- **Event acknowledgment** and deletion with Redis lock cleanup
- **Subscription management** with webhook URL support and wildcard matching
- **Delivery worker** (background async) with exponential backoff retry (7 attempts)
- **Dead letter queue** for events that exhaust all retry attempts
- **JWT authentication** with role-based access control
- **Health check** monitoring database and Redis connectivity
- **Metrics endpoint** with event counts by status and average delivery time

### Frontend (React + Vite)

- **Metrics panel** with auto-refresh showing event counts and delivery latency
- **Event explorer** with source/type filters, creation form, ack, delete, and status detail
- **Subscription manager** with CRUD operations
- **Health status indicator** showing API, database, and Redis connectivity
- API proxy from port 5004 to backend on port 3004

### Tests

- **45 tests** all passing
- Covers: event CRUD, inbox polling, filters, idempotency, ack/delete, subscriptions CRUD, matching logic, metrics, JWT auth, health check
- Uses SQLite in-memory + mocked Redis for fast isolated testing

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI (Python 3.11) |
| ORM | SQLAlchemy 1.4 (session.query style) |
| Database | PostgreSQL |
| Queue/Cache | Redis |
| Auth | JWT (python-jose + passlib) |
| Frontend | React 18 + Vite |
| Testing | pytest + FastAPI TestClient |

## Port Configuration

- API: 3004
- Frontend: 5004
- Database: zapier_triggers
- Redis: redis://localhost:6380

## Key Commands

```bash
make dev    # Start API server
make test   # Run tests (45 passing)
make seed   # Seed sample data
make build  # Install deps + build frontend
```
