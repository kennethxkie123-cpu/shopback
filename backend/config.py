import os
import sys
from dotenv import load_dotenv

load_dotenv()

INVOLVE_API_SECRET = os.getenv("INVOLVE_API_SECRET", "")
INVOLVE_API_KEY = os.getenv("INVOLVE_API_KEY", "")

# Validate critical secrets at startup
if not INVOLVE_API_KEY or not INVOLVE_API_SECRET:
    print("CRITICAL ERROR: INVOLVE_API_KEY and INVOLVE_API_SECRET must be set in .env")
    sys.exit(1)

INVOLVE_BASE_URL = os.getenv("INVOLVE_BASE_URL", "https://api.involve.asia")

# Resiliency & Performance Settings
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "3"))
CACHE_DURATION_SEC = int(os.getenv("CACHE_DURATION_SEC", "3600")) # Default 1 hour

# Security Settings
ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",")]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
