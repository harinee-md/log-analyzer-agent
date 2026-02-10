"""
Run the Log Analyzer Agent backend server.
"""

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
