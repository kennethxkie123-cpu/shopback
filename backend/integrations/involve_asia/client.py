import requests
import time
import logging
from typing import List, Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from backend.core.config import settings

logger = logging.getLogger(__name__)

class InvolveAsiaClient:
    """Client for Involve Asia Deeplink & Offers API."""
    
    def __init__(self):
        self.base_url = settings.INVOLVE_BASE_URL
        self.api_key = settings.INVOLVE_API_KEY
        self.api_secret = settings.INVOLVE_API_SECRET
        self.timeout = getattr(settings, "API_TIMEOUT", 10)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST", "GET"],
            backoff_factor=0.5
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self._token_cache = {"token": None, "expires_at": 0}
        self._offers_cache = {"data": None, "expires_at": 0}

    def authenticate(self) -> None:
        """Authenticates with Involve Asia API and caches token."""
        if self._token_cache["token"] and time.time() < self._token_cache["expires_at"]:
            return

        logger.info("Authenticating with Involve Asia API...")
        auth_url = f"{self.base_url}/api/authenticate"
        payload = {"key": self.api_key, "secret": self.api_secret}

        try:
            resp = self.session.post(auth_url, data=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            
            token = data.get("data", {}).get("token")
            if not token:
                raise ValueError("Failed to get token from Involve Asia response")
                
            self._token_cache["token"] = token
            self._token_cache["expires_at"] = time.time() + (110 * 60)
            self.session.headers["Authorization"] = f"Bearer {token}"
            logger.info("Involve Asia authentication successful")
        except requests.exceptions.RequestException as e:
            logger.error(f"Involve Asia authentication failed: {e}")
            if e.response is not None and e.response.status_code == 401:
                raise ValueError("Involve Asia Authentication Failed. Please check API Key and Secret.")
            raise ValueError("Failed to authenticate with Involve Asia API")

    def get_all_offers(self) -> List[Dict[str, Any]]:
        """Fetches all active offers with TTL cache."""
        if self._offers_cache["data"] is not None and time.time() < self._offers_cache["expires_at"]:
            return self._offers_cache["data"]

        self.authenticate()
        logger.info("Fetching offers from Involve Asia API...")
        
        try:
            payload = {
                "limit": 100,
                "filters[application_status]": "Approved",
                "filters[offer_status]": "Active"
            }
            resp = self.session.post(f"{self.base_url}/api/offers/all", data=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            offers = data.get("data", {}).get("data", [])
            
            self._offers_cache["data"] = offers
            self._offers_cache["expires_at"] = time.time() + 300
            
            logger.info(f"Successfully fetched {len(offers)} offers")
            return offers
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch offers: {e}")
            if e.response is not None:
                raise ValueError(f"Failed to fetch offers: API returned {e.response.status_code}")
            raise ValueError("Failed to reach Involve Asia API")

    def generate_deeplink(
        self,
        product_url: str,
        offer_id: int,
        aff_sub: Optional[str] = None,
        aff_sub2: Optional[str] = None,
        aff_sub3: Optional[str] = None,
        aff_sub4: Optional[str] = None,
        aff_sub5: Optional[str] = None
    ) -> str:
        """Generates an affiliate deeplink with sub-tracking parameters."""
        self.authenticate()
        payload = {"url": product_url, "offer_id": offer_id}
        if hasattr(settings, "INVOLVE_PROPERTY_ID") and settings.INVOLVE_PROPERTY_ID:
            payload["property_id"] = settings.INVOLVE_PROPERTY_ID

        if aff_sub: payload["aff_sub"] = aff_sub
        if aff_sub2: payload["aff_sub2"] = aff_sub2
        if aff_sub3: payload["aff_sub3"] = aff_sub3
        if aff_sub4: payload["aff_sub4"] = aff_sub4
        if aff_sub5: payload["aff_sub5"] = aff_sub5


        logger.info(f"Generating deeplink for offer_id={offer_id}, aff_sub={aff_sub}")
        try:
            response = self.session.post(f"{self.base_url}/api/deeplink/generate", data=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            affiliate_link = data.get("data", {}).get("tracking_link")
            if not affiliate_link:
                raise ValueError("Unexpected API response format")
                
            logger.info("Successfully generated deeplink")
            return affiliate_link
        except requests.exceptions.RequestException as e:
            logger.error(f"Deeplink generation failed: {e}")
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    msg = error_data.get("message", "API returned an empty error.")
                    raise ValueError(f"Failed to generate deeplink: {msg}")
                except ValueError as ve:
                    if "Failed to generate deeplink" in str(ve):
                        raise ve
                raise ValueError(f"Failed to generate deeplink: HTTP {e.response.status_code}")
            raise ValueError("Failed to reach Involve Asia API")

involve_client = InvolveAsiaClient()
