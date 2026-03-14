"""Event API routes — ingest, inbox, ack, delete, status."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.redis_client import get_redis
from app.auth import get_current_user
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventListResponse,
    EventAck,
    EventAckResponse,
    EventDeleteResponse,
    EventStatusResponse,
    DeliveryLogEntry,
)
from app.services.event_service import (
    create_event,
    get_inbox_events,
    ack_event,
    delete_event,
    get_event_status,
)

router = APIRouter(prefix="/v1", tags=["events"])


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new event",
    description="Submit an event for processing. Idempotent: duplicate events within 60s return the existing event.",
)
def ingest_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
    user=Depends(get_current_user),
):
    event, is_new = create_event(
        db=db,
        redis_client=redis_client,
        source=body.source,
        event_type=body.event_type,
        payload=body.payload,
    )
    if not is_new:
        # Return 200 for idempotent duplicate
        return event
    return event


@router.get(
    "/inbox",
    response_model=EventListResponse,
    summary="Pull undelivered events",
    description="Retrieve pending events for a consumer. Events are locked for 30s (visibility timeout).",
)
def get_inbox(
    consumer_id: str = Query(..., description="Consumer identifier"),
    event_type: str = Query(None, description="Filter by event type"),
    source: str = Query(None, description="Filter by source"),
    limit: int = Query(10, le=100, ge=1, description="Max events to return"),
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
    user=Depends(get_current_user),
):
    events = get_inbox_events(
        db=db,
        redis_client=redis_client,
        consumer_id=consumer_id,
        event_type=event_type,
        source=source,
        limit=limit,
    )
    return EventListResponse(
        events=[EventResponse.model_validate(e, from_attributes=True) for e in events],
        count=len(events),
    )


@router.post(
    "/events/{event_id}/ack",
    response_model=EventAckResponse,
    summary="Acknowledge event consumption",
    description="Mark an event as consumed. Removes the visibility timeout lock.",
)
def acknowledge_event(
    event_id: str,
    body: EventAck,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
    user=Depends(get_current_user),
):
    event = ack_event(db, redis_client, event_id, body.consumer_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return EventAckResponse(
        id=event.id,
        delivery_status=event.delivery_status.value,
        acked_at=event.acked_at,
    )


@router.delete(
    "/events/{event_id}",
    response_model=EventDeleteResponse,
    summary="Delete an event",
    description="Permanently remove an event and its delivery logs.",
)
def remove_event(
    event_id: str,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
    user=Depends(get_current_user),
):
    deleted = delete_event(db, redis_client, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return EventDeleteResponse(deleted=True, id=event_id)


@router.get(
    "/events/{event_id}/status",
    response_model=EventStatusResponse,
    summary="Get event delivery status",
    description="Returns event details with full delivery attempt history.",
)
def event_status(
    event_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    result = get_event_status(db, event_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    event = result["event"]
    logs = result["logs"]

    return EventStatusResponse(
        id=event.id,
        source=event.source,
        event_type=event.event_type,
        delivery_status=event.delivery_status.value,
        delivery_attempts=event.delivery_attempts,
        last_attempt_at=event.last_attempt_at,
        acked_at=event.acked_at,
        created_at=event.created_at,
        delivery_log=[
            DeliveryLogEntry(
                attempt=log.attempt_number,
                status_code=log.status_code,
                error=log.error_message,
                duration_ms=log.duration_ms,
                at=log.attempted_at,
            )
            for log in logs
        ],
    )
