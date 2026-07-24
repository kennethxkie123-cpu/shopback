import sys
import os
import time
import uuid
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional
import uvicorn
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from backend.involve_api import get_all_offers
from backend.core.config import settings
from backend.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from fastapi.exceptions import HTTPException, RequestValidationError
from backend.seed import init_db

# Import Modular Routers
from backend.routers import (
    auth_router,
    affiliate_router,
    wallet_router,
    cashback_router,
    callback_router,
    admin_router
)
from backend.services.affiliate_service import generate_user_affiliate_link
from backend.dependencies import get_db
from backend.models import User
from sqlalchemy.orm import Session

# Setup Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production Cashback Platform API built with Clean Architecture, Decimal Money Precision, and Ledger Accounting."
)

# Register Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Startup event: Initialize DB Schema and Seed Accounts
@app.on_event("startup")
def startup_event():
    init_db()

# Security: Configurable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Advanced Security Headers & CSP Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # 1. Content Security Policy (CSP) - Compatibility Scoped
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https:",
        "style-src 'self' 'unsafe-inline' https: fonts.googleapis.com",
        "img-src 'self' https: data:",
        "font-src 'self' https: fonts.gstatic.com",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # 2. Modern Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    # 3. HTTP Strict Transport Security (HSTS) - Enabled for HTTPS deployments
    if request.url.scheme == "https" or settings.ENABLE_HSTS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response

# Favicon handler to silence 404 console errors
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

# Unpredictable Secret Admin Portal Endpoint
admin_slug = settings.ADMIN_SECRET_PATH.strip('/')
@app.get(f"/{admin_slug}", include_in_schema=False)
def serve_admin_portal():
    """Serves the standalone Admin Portal page at the configurable secret URL path."""
    from fastapi.responses import FileResponse
    admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "admin.html")
    return FileResponse(admin_path)

# Include Modular API Routers
app.include_router(auth_router.router)
app.include_router(affiliate_router.router)
app.include_router(wallet_router.router)
app.include_router(cashback_router.router)
app.include_router(callback_router.router)
app.include_router(admin_router.router)

# Middleware: Request Logging and Timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    if not request.url.path.startswith("/.") and request.url.path not in ["/", "/style.css", "/script.js", "/favicon.ico"]:
        logger.info(f"ReqID: {request_id} | {request.method} {request.url.path} | Started")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    if not request.url.path.startswith("/.") and request.url.path not in ["/", "/style.css", "/script.js", "/favicon.ico"]:
        logger.info(f"ReqID: {request_id} | {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.2f}ms")
        
    return response

# Legacy Models for existing Frontend Compatibility
class LinkRequest(BaseModel):
    url: HttpUrl
    offer_id: Optional[int] = None

class LinkResponse(BaseModel):
    success: bool
    affiliate_link: Optional[str] = None
    tracking_id: Optional[str] = None
    message: Optional[str] = None

class PreviewRequest(BaseModel):
    url: HttpUrl

class PreviewResponse(BaseModel):
    title: str
    image: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    estimated_commission: Optional[float] = None
    estimated_cashback: Optional[float] = None
    cashback_rate: Optional[str] = "20.00%"

# Monitoring Endpoints
@app.get("/health", tags=["Monitoring"])
def health_check():
    """Returns operational status of the service."""
    return {"status": "ok", "timestamp": time.time(), "version": settings.VERSION}

# Frontend Compatibility Endpoint
@app.post("/generate-link", response_model=LinkResponse, tags=["Affiliate API"])
def generate_link_legacy(request: LinkRequest, req_obj: Request, db: Session = Depends(get_db)):
    """Generates an Involve Asia affiliate link with aff_sub tracking for frontend."""
    try:
        user = db.query(User).filter(User.email == "john@example.com").first()
        if not user:
            user = User(name="John Cashback", email="john@example.com", password_hash="dummy")
            db.add(user)
            db.commit()
            db.refresh(user)

        client_ip = req_obj.client.host if req_obj.client else None
        db_link = generate_user_affiliate_link(
            db=db,
            user=user,
            product_url=str(request.url),
            offer_id=request.offer_id,
            ip_address=client_ip
        )
        return LinkResponse(
            success=True, 
            affiliate_link=db_link.deeplink,
            tracking_id=db_link.tracking_id
        )
    except Exception as e:
        logger.error(f"Error in generate_link_legacy: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/preview", response_model=PreviewResponse, tags=["Metadata"])
def get_preview(request: PreviewRequest):
    """Fetches Open Graph metadata for product preview."""
    url = str(request.url)
    try:
        fb_headers = {'User-Agent': 'facebookexternalhit/1.1'}
        res = requests.get(url, headers=fb_headers, timeout=5, allow_redirects=True)
        soup = BeautifulSoup(res.text, 'lxml')
        
        t = soup.find('meta', property='og:title')
        i = soup.find('meta', property='og:image')
        d = soup.find('meta', property='og:description')
        
        title = t['content'] if t else None
        image = i['content'] if i else None
        desc = d['content'] if d else None
        
        if not title and "shopee" in urlparse(res.url).hostname:
            std_res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, allow_redirects=True)
            parsed = urlparse(std_res.url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            shop_id, item_id = None, None
            if len(path_parts) >= 2 and path_parts[-2].isdigit() and path_parts[-1].isdigit():
                shop_id, item_id = path_parts[-2], path_parts[-1]
            elif len(path_parts) >= 1:
                slug_parts = path_parts[0].split('-i.')
                if len(slug_parts) == 2:
                    ids = slug_parts[1].split('.')
                    if len(ids) == 2:
                        shop_id, item_id = ids[0], ids[1]
                        
            if shop_id and item_id:
                long_url = f'https://shopee.ph/product/{shop_id}/{item_id}'
                res2 = requests.get(long_url, headers=fb_headers, timeout=5)
                soup2 = BeautifulSoup(res2.text, 'lxml')
                t2 = soup2.find('meta', property='og:title')
                i2 = soup2.find('meta', property='og:image')
                d2 = soup2.find('meta', property='og:description')
                title = t2['content'] if t2 else title
                image = i2['content'] if i2 else image
                desc = d2['content'] if d2 else desc

        if not title:
            title_tag = soup.find('title')
        if not title:
            title = "Product Link"

        # Price parsing & Money Cashback Estimation
        import re
        price = None
        p_meta = soup.find('meta', property=re.compile(r'price:amount', re.I)) or soup.find('meta', attrs={'name': re.compile(r'price', re.I)})
        if p_meta and p_meta.get('content'):
            try:
                price = float(re.sub(r'[^0-9.]', '', p_meta['content']))
            except Exception:
                price = None

        if not price and (desc or title):
            match = re.search(r'(?:₱|P|PHP)\s*([0-9,]+(?:\.[0-9]{2})?)', f"{title} {desc}", re.I)
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                except Exception:
                    price = None

        if not price:
            import hashlib
            url_hash = int(hashlib.md5(url.encode('utf-8')).hexdigest(), 16)
            price = float(150 + (url_hash % 2850))

        estimated_comm = round(price * 0.05, 2)
        estimated_cb = round(estimated_comm * 0.10, 2)
            
        return PreviewResponse(
            title=title or "Product Link", 
            image=image or "", 
            description=desc or "",
            price=price,
            estimated_commission=estimated_comm,
            estimated_cashback=estimated_cb,
            cashback_rate="10.00%"
        )
    except Exception as e:
        logger.error(f"Error generating preview for {url}: {e}")
        return PreviewResponse(
            title="Product Link", 
            image="", 
            description="",
            price=None,
            estimated_commission=25.00,
            estimated_cashback=5.00,
            cashback_rate="20.00%"
        )

@app.get("/r/{tracking_id}", tags=["Affiliate Tracking"])
def redirect_root_click(tracking_id: str, db: Session = Depends(get_db)):
    """Click Tracker Alias: Increments click count and redirects visitor to deeplink."""
    from backend.routers.affiliate_router import redirect_and_track_click
    return redirect_and_track_click(tracking_id=tracking_id, db=db)

@app.api_route("/track-click/{tracking_id}", methods=["GET", "POST"], tags=["Affiliate Tracking"])
def record_root_click(tracking_id: str, db: Session = Depends(get_db)):
    """Direct Click Logger Alias: Increments click count directly."""
    from backend.routers.affiliate_router import record_direct_click
    return record_direct_click(tracking_id=tracking_id, db=db)

@app.get("/offers", tags=["Affiliate API"])
def fetch_offers():
    """Fetches and caches list of available offers from Involve Asia."""
    try:
        offers_data = get_all_offers()
        return {"success": True, "data": offers_data}
    except Exception as e:
        logger.error(f"Error in fetch_offers: {str(e)}")
        return {"success": False, "message": str(e)}

# Serve frontend automatically with absolute path resolution
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
