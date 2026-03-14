# Story 2: Inbox Polling (Pull-Based Consumption)

## As a consumer, I want to pull undelivered events from my inbox so I can process them at my own pace.

### Acceptance Criteria
- GET /v1/inbox returns pending events for a consumer_id
- Supports filtering by event_type and source
- Limit parameter (default 10, max 100)
- Events are soft-locked for 30 seconds on retrieval (visibility timeout)
- Locked events are not returned to other consumers
- Lock expires after 30s if not ACKed
- Returns event list with count

### Technical Notes
- Visibility timeout implemented via Redis key with TTL
- Lock key format: "lock:{event_id}" with value = consumer_id
- Query filters applied at database level
