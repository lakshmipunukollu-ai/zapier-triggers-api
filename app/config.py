"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zapier_triggers")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
ALGORITHM = "HS256"

# Delivery settings
VISIBILITY_TIMEOUT_SECONDS = 30
MAX_DELIVERY_ATTEMPTS = 7
RETRY_DELAYS = [1, 5, 30, 300, 1800, 7200, 28800]  # seconds
IDEMPOTENCY_WINDOW_SECONDS = 60
