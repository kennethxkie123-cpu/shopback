# Affiliate Link Generator

A production-ready FastAPI backend and Vanilla JS frontend tool to generate affiliate tracking links via the Involve Asia API.

## Features
- **Auto-detection**: Automatically detects the Offer ID based on the pasted Shopee or Lazada URL.
- **Resilient**: Features exponential backoff retries, connection pooling, and request timeouts.
- **Secure**: Strict URL validation, configurable CORS, and robust error handling.
- **Performant**: In-memory caching for offers and authentication tokens.
- **Observable**: Structured logging and health endpoints.

## Project Structure
- `backend/main.py`: FastAPI routing, middleware, and request validation.
- `backend/involve_api.py`: Business logic, retries, caching, and external API communication.
- `backend/config.py`: Environment variable loading and validation.
- `frontend/`: Vanilla HTML/JS/CSS client.
- `tests/`: Automated unit tests using `pytest` / `unittest`.

## Installation & Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install fastapi uvicorn requests python-dotenv pydantic httpx
   ```

2. Create a `.env` file in the root directory:
   ```ini
   INVOLVE_API_KEY=your_real_api_key
   INVOLVE_API_SECRET=your_real_api_secret
   INVOLVE_BASE_URL=https://api.involve.asia
   
   # Configurable options
   API_TIMEOUT=10
   RETRY_COUNT=3
   CACHE_DURATION_SEC=3600
   ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   LOG_LEVEL=INFO
   ```

3. Run the development server:
   ```bash
   uvicorn backend.main:app --reload --port 8001
   ```

## API Documentation

- `GET /health` - Returns the operational status of the service.
- `GET /offers` - Fetches and caches the available offers from your Involve Asia account.
- `POST /generate-link` - Generates a tracking link. 
  - Payload: `{"url": "https://shopee.ph/...", "offer_id": 5034}`

## Running Tests
Run the test suite using:
```bash
python -m unittest tests/test_app.py
```
