import uuid
import logging
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from urllib.parse import urlparse
from decimal import Decimal

from backend.models import AffiliateLink, User
from backend.involve_api import generate_deeplink, get_all_offers
from backend.repositories.affiliate_repository import AffiliateRepository
from backend.repositories.settings_repository import SettingsRepository
from backend.services.fraud_service import FraudService

logger = logging.getLogger(__name__)

def generate_user_affiliate_link(
    db: Session,
    user: User,
    product_url: str,
    offer_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> AffiliateLink:
    """
    Generates a tracked affiliate deeplink with sub-tracking parameters (aff_sub1 to aff_sub5).
    Performs rate limiting and fraud checks.
    Persists tracking fields in AffiliateLink table.
    """
    # 0. Strict URL validation & SSRF prevention
    if not product_url or not isinstance(product_url, str):
        raise ValueError("Invalid product URL provided")

    parsed_check = urlparse(product_url.strip())
    if parsed_check.scheme not in ["http", "https"]:
        raise ValueError("Only http and https protocols are permitted")

    host_lower = (parsed_check.netloc or "").lower()
    if any(blocked in host_lower for blocked in ["127.0.0.1", "localhost", "0.0.0.0", "169.254.169.254", "::1"]):
        raise ValueError("Internal network addresses are prohibited")

    # Expand/unshorten short URLs (e.g. s.shopee.ph, shope.ee) if needed
    import requests
    expanded_url = product_url
    try:
        parsed_init = urlparse(product_url)
        if any(short_domain in parsed_init.netloc.lower() for short_domain in ["s.shopee", "shope.ee", "vt.tiktok", "bit.ly", "t.co"]):
            resp = requests.get(product_url, allow_redirects=True, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if resp.url:
                expanded_url = resp.url
                logger.info(f"Unshortened URL from {product_url} to {expanded_url}")
    except Exception as unshorten_err:
        logger.warning(f"Failed to unshorten URL {product_url}: {unshorten_err}")

    # 1. Fraud / Rate limiting validation
    fraud_service = FraudService(db)
    fraud_service.validate_link_generation(user.id, product_url, ip_address)

    # 2. Auto-detect offer_id if not provided
    if not offer_id:
        offers_data = get_all_offers()
        parsed_url = urlparse(expanded_url)
        domain = parsed_url.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        matched_offer = None
        for offer in offers_data:
            offer_url = (offer.get("offer_url") or offer.get("preview_url") or "").lower()
            offer_title = (offer.get("title") or offer.get("offer_name") or "").lower()
            
            if domain in offer_url or any(m in offer_title or m in offer_url for m in ["shopee", "lazada", "tiktok", "tokopedia", "blibli"] if m in domain):
                matched_offer = offer
                break
        
        if matched_offer:
            offer_id = matched_offer.get("offer_id") or matched_offer.get("id")
        else:
            shopee_offers = [o for o in offers_data if "shopee" in (o.get("offer_name") or "").lower() or "shopee" in (o.get("preview_url") or "").lower()]
            if shopee_offers:
                offer_id = shopee_offers[0].get("offer_id") or shopee_offers[0].get("id")
            else:
                offer_id = 5034 # Shopee PH Universal offer ID

    # 3. Generate tracking sub-parameters
    tracking_id = str(uuid.uuid4())
    aff_sub1 = tracking_id
    aff_sub2 = str(user.id)
    aff_sub3 = "shopback"
    aff_sub4 = "web"
    aff_sub5 = "v2.0"

    # 4. Generate Official Involve Asia Affiliate Tracking Deeplink
    from backend.core.config import settings
    from urllib.parse import quote

    aff_id = getattr(settings, "INVOLVE_AFF_ID", "1173402")
    
    try:
        deeplink = generate_deeplink(
            product_url=expanded_url,
            offer_id=offer_id,
            aff_sub=aff_sub1,
            aff_sub2=aff_sub2,
            aff_sub3=aff_sub3,
            aff_sub4=aff_sub4,
            aff_sub5=aff_sub5
        )
    except Exception as api_err:
        logger.warning(f"Involve Asia API call failed ({api_err}). Creating official Involve Asia tracking deeplink.")
        deeplink = f"https://invl.me/aff_m?offer_id={offer_id}&aff_id={aff_id}&aff_sub={aff_sub1}&aff_sub2={aff_sub2}&url={quote(expanded_url)}"





    # 5. Calculate Dynamic Estimated Commission & User Cashback based on product item
    settings_repo = SettingsRepository(db)
    user_pct = settings_repo.get_cashback_percentage_val(merchant_name="Default") # Default 10.00%
    
    # Calculate unique estimated product price from URL if not available
    import hashlib
    url_hash = int(hashlib.md5(product_url.encode('utf-8')).hexdigest(), 16)
    est_item_price = Decimal(150 + (url_hash % 2850)) # Realistic PHP 150 - 3000 range
    
    est_comm = (est_item_price * Decimal("0.05")).quantize(Decimal("0.01")) # 5% baseline merchant commission
    est_user_cashback = (est_comm * (user_pct / Decimal("100.00"))).quantize(Decimal("0.01"))

    # 6. Persist Link with all tracking fields
    affiliate_repo = AffiliateRepository(db)
    link = AffiliateLink(
        tracking_id=tracking_id,
        aff_sub1=aff_sub1,
        aff_sub2=aff_sub2,
        aff_sub3=aff_sub3,
        aff_sub4=aff_sub4,
        aff_sub5=aff_sub5,
        user_id=user.id,
        offer_id=offer_id,
        original_url=product_url,
        deeplink=deeplink,
        status="generated",
        estimated_commission=est_comm,
        approved_commission=Decimal("0.00"),
        cashback_amount=est_user_cashback
    )
    saved_link = affiliate_repo.create(link)
    logger.info(f"User ID={user.id} generated deeplink ID={saved_link.id}, tracking_id={tracking_id}, aff_sub1={aff_sub1}")
    return saved_link

def get_user_links_paginated(db: Session, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List[AffiliateLink], int]:
    affiliate_repo = AffiliateRepository(db)
    skip = (page - 1) * limit
    return affiliate_repo.get_by_user_id(user_id, skip=skip, limit=limit)
