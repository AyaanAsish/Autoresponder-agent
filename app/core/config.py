"""
Configuration settings loaded from environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file (look in project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Ollama Cloud settings
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# Gmail OAuth settings
GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN: str = os.getenv("GMAIL_REFRESH_TOKEN", "")

# Token file paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE: str = os.getenv("TOKEN_FILE", str(PROJECT_ROOT / "token.json"))
CREDENTIALS_FILE: str = os.getenv("CREDENTIALS_FILE", str(PROJECT_ROOT / "app" / "credentials.json"))

# Gmail API Scopes
GMAIL_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def validate_config() -> dict[str, bool]:
    """Validate that required configuration is present."""
    return {
        "ollama_api_key": bool(OLLAMA_API_KEY),
        "ollama_base_url": bool(OLLAMA_BASE_URL),
        "ollama_model": bool(OLLAMA_MODEL),
        "gmail_client_id": bool(GMAIL_CLIENT_ID),
        "gmail_client_secret": bool(GMAIL_CLIENT_SECRET),
    }
