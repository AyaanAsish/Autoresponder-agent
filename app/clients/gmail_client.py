"""
Gmail API Client with OAuth2 authentication.
Supports both local server flow and manual authorization code flow.
"""
import os
import json
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

from app.core.config import (
    GMAIL_CLIENT_ID,
    GMAIL_CLIENT_SECRET,
    GMAIL_SCOPES,
    TOKEN_FILE,
    CREDENTIALS_FILE,
)


# Global service instance
_gmail_service: Optional[Resource] = None


def get_oauth_config() -> dict:
    """Get OAuth client configuration."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    
    if not GMAIL_CLIENT_ID or not GMAIL_CLIENT_SECRET:
        raise ValueError(
            "Gmail credentials not found. Either provide credentials.json "
            "or set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET environment variables."
        )
    
    return {
        "installed": {
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
        }
    }


def generate_auth_url(redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> tuple[str, Flow]:
    """
    Generate Gmail OAuth authorization URL.
    
    Args:
        redirect_uri: The redirect URI for OAuth callback.
                     Use "urn:ietf:wg:oauth:2.0:oob" for manual code entry.
                     Use "http://localhost:PORT/auth/callback" for automatic flow.
    
    Returns:
        Tuple of (authorization_url, flow_object)
    """
    config = get_oauth_config()
    
    flow = Flow.from_client_config(
        config,
        scopes=GMAIL_SCOPES,
        redirect_uri=redirect_uri
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    
    return auth_url, flow


def exchange_code_for_token(flow: Flow, authorization_code: str) -> dict:
    """
    Exchange authorization code for access token.
    
    Args:
        flow: The OAuth flow object from generate_auth_url
        authorization_code: The code received from Google after authorization
        
    Returns:
        Token information dict
    """
    flow.fetch_token(code=authorization_code)
    creds = flow.credentials
    
    # Save token
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes),
        'universe_domain': getattr(creds, 'universe_domain', 'googleapis.com'),
        'account': '',
        'expiry': creds.expiry.isoformat() + 'Z' if creds.expiry else None
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    
    # Reset global service to use new credentials
    global _gmail_service
    _gmail_service = None
    
    return token_data


def create_token_from_code(authorization_code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> dict:
    """
    Create token.json from authorization code (one-step process).
    
    Args:
        authorization_code: The code from Google OAuth
        redirect_uri: Must match the URI used when generating the auth URL
        
    Returns:
        Token information dict
    """
    config = get_oauth_config()
    
    flow = Flow.from_client_config(
        config,
        scopes=GMAIL_SCOPES,
        redirect_uri=redirect_uri
    )
    
    return exchange_code_for_token(flow, authorization_code)


def check_token_status() -> dict:
    """
    Check the status of the current OAuth token.
    
    Returns:
        Dict with token status information
    """
    if not os.path.exists(TOKEN_FILE):
        return {
            "exists": False,
            "valid": False,
            "message": "token.json not found"
        }
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
        
        if creds.valid:
            return {
                "exists": True,
                "valid": True,
                "expired": False,
                "has_refresh_token": bool(creds.refresh_token),
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "message": "Token is valid"
            }
        elif creds.expired and creds.refresh_token:
            return {
                "exists": True,
                "valid": False,
                "expired": True,
                "has_refresh_token": True,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "message": "Token expired but can be refreshed"
            }
        else:
            return {
                "exists": True,
                "valid": False,
                "expired": True,
                "has_refresh_token": False,
                "message": "Token expired and cannot be refreshed"
            }
    except Exception as e:
        return {
            "exists": True,
            "valid": False,
            "error": str(e),
            "message": f"Token file exists but is invalid: {e}"
        }


def refresh_token() -> dict:
    """
    Manually refresh the OAuth token.
    
    Returns:
        Dict with refresh status
    """
    if not os.path.exists(TOKEN_FILE):
        return {"success": False, "error": "token.json not found"}
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
        
        if not creds.refresh_token:
            return {"success": False, "error": "No refresh token available"}
        
        creds.refresh(Request())
        
        # Save refreshed token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        
        # Reset global service
        global _gmail_service
        _gmail_service = None
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_token() -> dict:
    """
    Delete the current token.json file.
    
    Returns:
        Dict with deletion status
    """
    global _gmail_service
    _gmail_service = None
    
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        return {"success": True, "message": "token.json deleted"}
    return {"success": True, "message": "token.json did not exist"}


def get_gmail_service(force_refresh: bool = False) -> Resource:
    """
    Authenticate and return Gmail API service.
    
    Uses token.json if available, otherwise raises an error
    (use the /auth endpoints to generate token first).
    
    Args:
        force_refresh: Force token refresh even if valid
        
    Returns:
        Gmail API service resource.
    """
    global _gmail_service
    
    if _gmail_service and not force_refresh:
        return _gmail_service
    
    creds: Optional[Credentials] = None

    # Check for existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
    else:
        raise ValueError(
            "token.json not found. Use /auth/url to get authorization URL, "
            "then /auth/callback with the code to generate token."
        )

    # Refresh if needed
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        else:
            raise ValueError(
                "Token is invalid and cannot be refreshed. "
                "Use /auth/url to re-authorize."
            )

    _gmail_service = build("gmail", "v1", credentials=creds)
    return _gmail_service


def test_gmail_connection(service: Resource = None) -> tuple[bool, str]:
    """
    Test Gmail API connection by fetching user profile.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        if service is None:
            service = get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "unknown")
        return True, f"Connected as {email}"
    except Exception as e:
        return False, str(e)
