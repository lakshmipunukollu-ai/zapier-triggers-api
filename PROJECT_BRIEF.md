# PROJECT BRIEF
# (Extracted from MASTER_PROJECT_PLAYBOOK.md — your section only)

## SENIOR ENGINEER DECISIONS — READ FIRST

Before any code is written, here are the opinionated decisions made across all 9 projects
and why. An agent should never second-guess these unless given new information.

### Stack choices made
| Project | Backend | Frontend | DB | Deploy | Rationale |
|---------|---------|---------|-----|--------|-----------|
| FSP Scheduler | TypeScript + Node.js | React + TypeScript | PostgreSQL (multi-tenant) | Azure Container Apps | TS chosen over C# — same Azure ecosystem, better AI library support, faster iteration |
| Replicated | Python + FastAPI | Next.js 14 | PostgreSQL + S3 | Docker | Python wins for LLM tooling; Next.js for real-time streaming UI |
| ServiceCore | Node.js + Express | Angular (required) | PostgreSQL | Railway | Angular required — clean REST API behind it |
| Zapier | Python + FastAPI | None (API only + optional React dashboard) | PostgreSQL + Redis | Railway | Redis for event queue durability; Python for DX-first API |
| ST6 | Java 21 + Spring Boot | TypeScript micro-frontend (React) | PostgreSQL | Docker | Java required — Spring Boot is the senior choice; React micro-frontend mounts into PA host |
| ZeroPath | Python + FastAPI | React + TypeScript | PostgreSQL | Render | Python for LLM scanning logic; React for triage dashboard |
| Medbridge | Python + FastAPI + LangGraph | None (webhook-driven) | PostgreSQL | Railway | LangGraph is the correct tool for state-machine AI agents |
| CompanyCam | Python + FastAPI | React + TypeScript | PostgreSQL | Render | Python for CV/ML inference; React for annotation UI |
| Upstream | Django + DRF | React + TypeScript | PostgreSQL | Render | Django for rapid e-commerce scaffolding; built-in admin is a bonus |

### The 4 shared modules — build these FIRST
These are the highest ROI pieces of work. Build them once, copy-scaffold into every project.

1. `shared/llm_client.py` — Claude API wrapper with retry, streaming, structured output parsing
2. `shared/auth/` — JWT auth + role-based guards (Python + TypeScript versions)
3. `shared/state_machine.py` — Generic FSM: states, transitions, guards, event log
4. `shared/queue/` — Job queue pattern: enqueue, dequeue, ack, retry (Redis + Postgres fallback)

### Build order (wave system)
**Wave 0 (Day 1):** Build shared modules. All other waves depend on these.
**Wave 1 (Days 2-3):** Zapier + ZeroPath — establish LLM pipeline + REST API patterns
**Wave 2 (Days 4-5):** Medbridge + Replicated — LLM pipeline variants, more complex AI
**Wave 3 (Days 6-8):** FSP + ST6 — complex business logic, approval flows
**Wave 4 (Days 9-11):** ServiceCore + Upstream + CompanyCam — isolated stacks, finish strong

---

## PROJECT 4: ZAPIER — TRIGGERS API
**Company:** Zapier | **Stack:** Python + FastAPI + Redis + PostgreSQL

### Company mission to impress
Zapier's mission is to make automation accessible to everyone. The TriggersAPI is their
next platform primitive. What will impress them: developer experience excellence, reliability
thinking, and the ability to reason about distributed systems trade-offs. Write an API so
clean that it feels like something Zapier themselves would ship. Document every trade-off.

### Architecture
```
Railway
├── api (Python + FastAPI)
│   ├── POST /v1/events                — ingest event from any source
│   ├── GET  /v1/inbox                 — pull undelivered events (consumer)
│   ├── POST /v1/events/:id/ack        — mark event as consumed
│   ├── DELETE /v1/events/:id         — delete after consumption
│   ├── POST /v1/subscriptions         — subscribe to event types/sources
│   ├── GET  /v1/events/:id/status     — delivery status + retry history
│   └── GET  /v1/metrics              — event counts, latency, delivery rates
├── delivery-worker (Python + Celery/Redis)
│   ├── PushDelivery                   — deliver to registered webhook URLs
│   ├── RetryScheduler                 — exponential backoff retry
│   └── DeadLetterHandler             — move failed events after N retries
└── dashboard (optional React)
    └── EventExplorer                  — visualize event flow, retry status
```

### Event model — the core data structure, get this right
```python
class Event(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:16]}")
    source: str                  # "github.com" | "stripe" | "custom-app"
    event_type: str              # "push" | "payment.succeeded" | "order.created"
    payload: dict
    metadata: EventMetadata

class EventMetadata(BaseModel):
    received_at: datetime = Field(default_factory=datetime.utcnow)
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    delivery_attempts: int = 0
    last_attempt_at: datetime | None = None
    acked_at: datetime | None = None
    consumer_id: str | None = None

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKED = "acked"
    FAILED = "failed"
    DEAD = "dead"          # exhausted retries
```

### Reliability — the trade-off doc Zapier will read
```python
"""
DELIVERY GUARANTEE CHOICE: At-least-once delivery

Why not exactly-once:
- Exactly-once requires distributed transactions (2PC) across the event store and
  delivery record. This adds significant latency and operational complexity.
- At-least-once is achievable with an idempotency key (event.id) that consumers
  can use to deduplicate on their end.
- This mirrors how Stripe webhooks and AWS SQS work — the right call for a v1 API.

Idempotency: POST /events is idempotent on source+event_type+payload hash.
Duplicate submissions within a 60-second window return the existing event ID.

Retry policy: exponential backoff — 1s, 5s, 30s, 5min, 30min, 2hr, 8hr (7 attempts).
After 7 failures, event moves to dead-letter queue for inspection.
"""
```

### /inbox endpoint — the key consumer-facing API
```python
@router.get("/v1/inbox")
async def get_inbox(
    consumer_id: str = Query(...),
    event_type: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Pull-based event retrieval. Returns undelivered events for this consumer.
    Events are locked (soft-reserved) for 30 seconds to prevent double-delivery.
    Consumer must ACK within 30s or event becomes available again.
    
    This mirrors the SQS visibility timeout pattern — battle-tested for reliability.
    """
    query = select(Event).where(
        Event.delivery_status == DeliveryStatus.PENDING,
        Event.consumer_id.is_(None) | (Event.locked_until < datetime.utcnow()),
    )
    if event_type:
        query = query.where(Event.event_type == event_type)
    if source:
        query = query.where(Event.source == source)
    
    events = await db.execute(query.limit(limit))
    # Lock events for 30s
    await lock_events([e.id for e in events], consumer_id, redis)
    return {"events": events, "count": len(events)}
```

### CLAUDE.md for Zapier agent
```
You are a senior Python engineer building the TriggersAPI for Zapier.

COMPANY MISSION: Make automation accessible to everyone.
This API is a platform primitive — it will be used by millions of integrations.
Think about DX (developer experience) as a first-class requirement.

WHAT WILL IMPRESS THEM:
1. API is self-evident — great route naming, consistent response shapes, clear errors
2. Reliability thinking is documented — delivery guarantees, retry policy, idempotency
3. OpenAPI spec is complete and accurate (FastAPI auto-generates this — keep it clean)
4. The trade-off doc (MY_APPROACH_AND_THOUGHTS.md or similar) shows system design depth

DELIVERY GUARANTEE: At-least-once with idempotency keys. Document why, not just what.
RETRY POLICY: Exponential backoff, 7 attempts, then dead-letter queue.
LOCK PATTERN: SQS-style visibility timeout (30s) on /inbox to prevent double-delivery.

NEVER: Invent your own queue when Redis/Celery works perfectly
ALWAYS: Return event.id on ingestion, include delivery_status in every response
```

---


## SHARED MODULES — BUILD THESE IN WAVE 0

### shared/llm_client.py
```python
"""
Shared Claude API client. Used by: Replicated, ZeroPath, Medbridge, CompanyCam, FSP, Upstream.
Copy this file into each Python project that needs it.
"""
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import json

client = anthropic.Anthropic()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def complete(
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    as_json: bool = False,
) -> str | dict:
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    if as_json:
        # Strip markdown fences if present
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(clean)
    return text

async def analyze_image(
    image_b64: str,
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return json.loads(message.content[0].text)
```

### shared/auth.py (Python version)
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(user_id: str, role: str) -> str:
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY, algorithm=ALGORITHM
    )

def require_role(*roles: str):
    def dependency(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("role") not in roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return dependency

# Usage: @router.get("/admin", dependencies=[Depends(require_role("admin", "manager"))])
```

### shared/state_machine.py
```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable
from datetime import datetime

S = TypeVar('S')  # State type
E = TypeVar('E')  # Event type

@dataclass
class Transition(Generic[S, E]):
    from_state: S
    event: E
    to_state: S
    guard: Callable | None = None  # optional condition function

class StateMachine(Generic[S, E]):
    def __init__(self, initial: S, transitions: list[Transition]):
        self.state = initial
        self._transitions = {(t.from_state, t.event): t for t in transitions}
        self._log: list[dict] = []

    def transition(self, event: E, context: dict = None) -> S:
        key = (self.state, event)
        t = self._transitions.get(key)
        if not t:
            raise ValueError(f"Invalid transition: {self.state} + {event}")
        if t.guard and not t.guard(context or {}):
            raise ValueError(f"Guard failed: {self.state} + {event}")
        prev = self.state
        self.state = t.to_state
        self._log.append({"from": prev, "event": event, "to": self.state, "at": datetime.utcnow().isoformat()})
        return self.state

    @property
    def history(self) -> list[dict]:
        return self._log.copy()
```

---
