"""Redis client for event queue and locking."""
import redis
from app.config import REDIS_URL

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    """Dependency that returns the Redis client."""
    return redis_client
