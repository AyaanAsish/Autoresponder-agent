"""
Email utility functions for parsing and creating email messages.
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


def extract_email_body(payload: dict, max_length: int = 3000) -> str:
    """
    Extract plain text body from Gmail message payload.
    
    Args:
        payload: Gmail message payload dict
        max_length: Maximum characters to return
        
    Returns:
        Decoded email body text, truncated to max_length
    """
    # Direct body data
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")
        return body[:max_length]

    # Multipart message - look for text/plain
    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(
                part["body"]["data"]
            ).decode("utf-8", errors="ignore")
            return body[:max_length]
        
        # Nested multipart
        if mime_type.startswith("multipart/"):
            nested_body = extract_email_body(part, max_length)
            if nested_body:
                return nested_body

    return ""


def parse_email_address(from_header: str) -> str:
    """
    Extract email address from From header.
    
    Args:
        from_header: From header value like "John Doe <john@example.com>"
        
    Returns:
        Clean email address
    """
    if "<" in from_header and ">" in from_header:
        return from_header.split("<")[-1].rstrip(">").strip()
    return from_header.strip()


def create_reply_message(
    to_address: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None
) -> dict:
    """
    Create a properly formatted reply message for Gmail API.
    
    Args:
        to_address: Recipient email address
        subject: Email subject (will add Re: if not present)
        body: Reply body text
        thread_id: Optional thread ID for threading
        
    Returns:
        Dict with 'raw' encoded message and optional 'threadId'
    """
    msg = MIMEMultipart()
    msg["To"] = to_address
    
    # Add Re: prefix if not present
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    msg["Subject"] = subject
    
    msg.attach(MIMEText(body, "plain"))
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    
    result = {"raw": raw}
    if thread_id:
        result["threadId"] = thread_id
    
    return result
