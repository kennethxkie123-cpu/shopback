import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.involve_api import _token_cache, _offers_cache

client = TestClient(app)

class TestAffiliateLinkAPI(unittest.TestCase):
    
    def setUp(self):
        # Clear caches before each test
        _token_cache["token"] = None
        _token_cache["expires_at"] = 0
        _offers_cache["data"] = None
        _offers_cache["expires_at"] = 0
        
    def test_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_invalid_url_validation(self):
        # Should reject local hostnames and invalid schemes
        response = client.post("/generate-link", json={
            "url": "http://localhost:8000/test",
            "offer_id": 123
        })
        self.assertEqual(response.status_code, 422) # Unprocessable Entity
        
        response = client.post("/generate-link", json={
            "url": "ftp://test.com/file",
            "offer_id": 123
        })
        self.assertEqual(response.status_code, 422)

    @patch('backend.involve_api.requests.Session.post')
    def test_successful_generate_link(self, mock_post):
        # Setup mock responses: First for auth, second for generate link
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"data": {"token": "fake-token"}}
        
        mock_gen_response = MagicMock()
        mock_gen_response.status_code = 200
        mock_gen_response.json.return_value = {"data": {"tracking_link": "https://invol.co/aff_link"}}
        
        mock_post.side_effect = [mock_auth_response, mock_gen_response]
        
        response = client.post("/generate-link", json={
            "url": "https://shopee.com.my/product-test",
            "offer_id": 5034
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["affiliate_link"], "https://invol.co/aff_link")
        
    @patch('backend.involve_api.requests.Session.post')
    def test_auth_failure(self, mock_post):
        # Setup mock response for auth failure
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 401
        # Raise HTTPError to simulate requests behavior
        import requests
        err = requests.exceptions.HTTPError()
        err.response = mock_auth_response
        mock_post.side_effect = err
        
        response = client.post("/generate-link", json={
            "url": "https://shopee.com.my/product-test",
            "offer_id": 5034
        })
        
        self.assertEqual(response.status_code, 200) # Our API always returns 200 with success=False
        self.assertFalse(response.json()["success"])
        self.assertIn("Authentication Failed", response.json()["message"])

if __name__ == '__main__':
    unittest.main()
