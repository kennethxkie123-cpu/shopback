import sys
import os

# Add the root directory to sys path just in case
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
