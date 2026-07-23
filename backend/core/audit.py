import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import json

logger = logging.getLogger("audit")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [AUDIT] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

SENSITIVE_KEYS = {
    "password", "password_hash", "access_token", "token", "jwt",
    "secret", "api_key", "authorization", "cookie", "set-cookie"
}

def sanitize_audit_data(data: Any) -> Any:
    """Recursively masks sensitive values from being recorded in audit logs."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if k.lower() in SENSITIVE_KEYS:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_audit_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_audit_data(item) for item in data]
    return data

class AuditLogger:
    @staticmethod
    def log(
        action: str,
        user_id: Optional[Any] = None,
        resource: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Records an immutable audit log entry.
        Guarantees sensitive data (passwords, tokens, API keys) are masked.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": str(user_id) if user_id is not None else "anonymous",
            "resource": resource or "N/A",
            "client_ip": client_ip or "unknown",
            "user_agent": user_agent or "unknown",
            "result": result
        }

        if details:
            entry["details"] = sanitize_audit_data(details)

        try:
            log_str = json.dumps(entry)
            logger.info(log_str)
        except Exception as err:
            logger.error(f"Failed to record audit log: {err}")
