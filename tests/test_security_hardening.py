import sys
import os
import unittest
import json
import time
import hmac
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.security import create_access_token, is_token_revoked, revoke_token
from backend.core.audit import sanitize_audit_data, AuditLogger
from backend.core.config import settings

class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_security_headers_and_csp(self):
        """Verify presence of CSP, HSTS logic, X-Frame-Options, and security headers."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        headers = response.headers

        # Verify CSP
        self.assertIn("Content-Security-Policy", headers)
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("object-src 'none'", headers["Content-Security-Policy"])

        # Verify Modern Security Headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("geolocation=()", headers.get("Permissions-Policy", ""))
        self.assertEqual(headers.get("Cross-Origin-Opener-Policy"), "same-origin-allow-popups")

    def test_audit_data_masking(self):
        """Verify AuditLogger masks sensitive credentials and secrets."""
        raw_details = {
            "user_id": 42,
            "password": "SuperSecretPassword123!",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "api_key": "inv_secret_9988",
            "nested": {
                "secret": "hidden_value",
                "normal_field": "public_data"
            }
        }

        cleaned = sanitize_audit_data(raw_details)
        self.assertEqual(cleaned["user_id"], 42)
        self.assertEqual(cleaned["password"], "[REDACTED]")
        self.assertEqual(cleaned["access_token"], "[REDACTED]")
        self.assertEqual(cleaned["api_key"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["secret"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["normal_field"], "public_data")

    def test_token_revocation(self):
        """Verify token revocation blacklists logged-out tokens."""
        token = create_access_token(data={"sub": "test-uuid-99", "email": "john@example.com", "role": "user"})
        self.assertFalse(is_token_revoked(token))

        revoke_token(token)
        self.assertTrue(is_token_revoked(token))

        # Attempt API request with revoked token
        response = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        err_msg = response.json().get("message") or response.json().get("detail") or ""
        self.assertIn("Token has been revoked", err_msg)

    def test_callback_stale_timestamp_rejection(self):
        """Verify stale callbacks (>5 mins) are rejected to prevent replay attacks."""
        stale_ts = str(time.time() - 600) # 10 minutes ago
        payload = {
            "conversion_id": "conv_test_stale_123",
            "aff_sub1": "trk_non_existent",
            "commission": "10.00",
            "cashback": "2.00",
            "status": "approved",
            "merchant": "Shopee"
        }

        response = self.client.post(
            "/api/callback/conversion",
            json=payload,
            headers={"X-Timestamp": stale_ts}
        )
        self.assertEqual(response.status_code, 400)
        err_msg = response.json().get("message") or response.json().get("detail") or ""
        self.assertIn("timestamp expired", err_msg.lower())

if __name__ == "__main__":
    unittest.main()
