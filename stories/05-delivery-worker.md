# Story 5: Delivery Worker (Push + Retry)

## As the system, I want to deliver events to webhook URLs with retry logic.

### Acceptance Criteria
- Background worker processes pending events from Redis queue
- Matches events against active subscriptions with webhook_url
- POSTs event payload to webhook URL
- Logs delivery attempt (status code, response, duration)
- On failure: schedules retry with exponential backoff
- Retry schedule: 1s, 5s, 30s, 5min, 30min, 2hr, 8hr (7 attempts)
- After 7 failures: moves to dead-letter (status = "dead")
- Updates delivery_status and delivery_attempts on each try

### Technical Notes
- Uses asyncio background task, not Celery
- httpx for async HTTP delivery
- Delivery logs stored in delivery_logs table
