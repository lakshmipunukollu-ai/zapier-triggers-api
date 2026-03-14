# Story 4: Subscriptions (Webhook Push Delivery)

## As a developer, I want to subscribe to event types and receive them via webhook.

### Acceptance Criteria
- POST /v1/subscriptions creates a new subscription
- Requires consumer_id; optional event_type, source, webhook_url
- GET /v1/subscriptions lists subscriptions for a consumer
- Subscriptions with webhook_url enable push delivery
- Subscriptions can be activated/deactivated
- JWT authentication required

### Technical Notes
- Subscription matching: event_type and source filters (NULL = match all)
- Webhook delivery happens asynchronously via background worker
