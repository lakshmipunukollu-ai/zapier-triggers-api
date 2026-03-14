# Story 3: Event Acknowledgment & Deletion

## As a consumer, I want to acknowledge or delete events after processing them.

### Acceptance Criteria
- POST /v1/events/:id/ack marks event as "acked"
- Requires consumer_id in request body
- Sets acked_at timestamp
- Removes Redis lock
- DELETE /v1/events/:id removes event from database
- Returns confirmation response
- Both endpoints require JWT authentication
