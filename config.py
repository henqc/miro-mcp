import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MIRO_CLIENT_ID = os.getenv("MIRO_CLIENT_ID")
MIRO_CLIENT_SECRET = os.getenv("MIRO_CLIENT_SECRET")
MIRO_REDIRECT_URL = os.getenv("MIRO_REDIRECT_URL", "http://localhost:8080/callback")

TOKEN_STORAGE_DIR = Path.home() / ".miro-mcp"
TOKEN_STORAGE_FILE = TOKEN_STORAGE_DIR / "tokens.json"

TOKEN_STORAGE_DIR.mkdir(exist_ok=True)


def validate_config():
    # Validate required environment variables are set
    if not MIRO_CLIENT_ID:
        raise ValueError("MIRO_CLIENT_ID environment variable is required")
    if not MIRO_CLIENT_SECRET:
        raise ValueError("MIRO_CLIENT_SECRET environment variable is required")
