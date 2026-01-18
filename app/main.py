"""
FastAPI - Ayaan's Gmail Autoresponder Agent - Main Entry Point

Provides REST API endpoints for:
- OAuth authentication and token management
- Listing emails
- Reading emails with auto-generated draft replies
- Sending email replies
- AI agent chat interface
- Prometheus metrics
- Workflow diagram visualization
"""

from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.core.config import validate_config
from app.clients import (
    get_gmail_service,
    get_ollama_client,
    generate_auth_url,
    create_token_from_code,
    check_token_status,
    refresh_token,
    delete_token,
    test_gmail_connection,
)
from app.utils import MailboxSession, metrics_collector, get_metrics_output, generate_html_diagram
from app.agents import GmailAgent


# =========================
# Shared State
# =========================
class AppState:
    """Application state container."""
    gmail_service = None
    ollama_client = None
    mailbox: Optional[MailboxSession] = None
    agent: Optional[GmailAgent] = None
    # Store OAuth flow for callback
    oauth_flow = None


state = AppState()


# =========================
# Lifespan Management
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    print("🚀 Starting Ayaan's Gmail Autoresponder Agent...")
    
    # Validate configuration
    config_status = validate_config()
    missing = [k for k, v in config_status.items() if not v]
    if missing:
        print(f"⚠️  Missing configuration: {', '.join(missing)}")
    
    # Initialize Ollama client
    try:
        state.ollama_client = get_ollama_client()
        success, msg = state.ollama_client.test_connection()
        if success:
            print(f"✅ Ollama connected: {msg[:50]}...")
            metrics_collector.set_ollama_status(True)
        else:
            print(f"⚠️  Ollama connection issue: {msg}")
            metrics_collector.set_ollama_status(False)
    except Exception as e:
        print(f"❌ Ollama initialization failed: {e}")
        metrics_collector.set_ollama_status(False)
    
    # Check token status
    token_status = check_token_status()
    if token_status.get("valid"):
        print("✅ Gmail token found and valid")
        metrics_collector.set_token_status(True)
        try:
            state.gmail_service = get_gmail_service()
            print("✅ Gmail service initialized")
        except Exception as e:
            print(f"⚠️  Gmail service init failed: {e}")
    else:
        print(f"⚠️  Gmail token: {token_status.get('message')}")
        print("   Use /auth/url to get authorization URL")
        metrics_collector.set_token_status(False)
    
    # Initialize mailbox session
    state.mailbox = MailboxSession()
    print("✅ Mailbox session ready")
    
    # Initialize agent if both services available
    if state.gmail_service and state.ollama_client:
        state.agent = GmailAgent(
            ollama_client=state.ollama_client,
            gmail_service=state.gmail_service,
            mailbox=state.mailbox
        )
        print("✅ Gmail Agent ready")
    
    print("🎉 Ayaan's Gmail Agent is ready!")
    print("📖 API Docs: http://localhost:8000/docs")
    print("📊 Metrics: http://localhost:8000/metrics")
    print("📈 Workflow Diagram: http://localhost:8000/workflow-diagram")
    yield
    
    # Cleanup
    print("👋 Shutting down Ayaan's Gmail Agent...")


# =========================
# FastAPI App
# =========================
app = FastAPI(
    title="Ayaan's Gmail Autoresponder Agent",
    description="AI-powered Gmail assistant with OAuth authentication and auto-reply generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Request/Response Models
# =========================
class ListEmailsRequest(BaseModel):
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum emails to return")
    query: str = Field(default="is:unread", description="Gmail search query")


class ReadEmailRequest(BaseModel):
    email_number: int = Field(..., ge=1, description="Email number from list")
    generate_draft: bool = Field(default=True, description="Generate AI draft reply")
    tone: str = Field(default="normal", description="Reply tone: normal, friendly, or professional")


class RegenerateDraftRequest(BaseModel):
    email_number: int = Field(..., ge=1, description="Email number from list")
    tone: str = Field(default="normal", description="Reply tone: normal, friendly, or professional")


class SendReplyRequest(BaseModel):
    email_number: int = Field(..., ge=1, description="Email number to reply to")
    reply_body: Optional[str] = Field(default=None, description="Custom reply (uses draft if empty)")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message to the agent")


class ChatResponse(BaseModel):
    response: str
    conversation_length: int


class AuthCallbackRequest(BaseModel):
    code: str = Field(..., description="Authorization code from Google")
    redirect_uri: str = Field(
        default="urn:ietf:wg:oauth:2.0:oob",
        description="Redirect URI used when generating auth URL"
    )


class AuthUrlResponse(BaseModel):
    auth_url: str
    redirect_uri: str
    instructions: str


class TokenStatusResponse(BaseModel):
    exists: bool
    valid: bool
    expired: Optional[bool] = None
    has_refresh_token: Optional[bool] = None
    expiry: Optional[str] = None
    email: Optional[str] = None
    message: str


# =========================
# Health & Status Endpoints
# =========================
@app.get("/health")
async def health_check():
    """Check service health."""
    token_status = check_token_status()
    return {
        "status": "healthy",
        "agent": "Ayaan's Gmail Autoresponder Agent",
        "gmail_token_valid": token_status.get("valid", False),
        "gmail_connected": state.gmail_service is not None,
        "ollama_connected": state.ollama_client is not None,
        "agent_ready": state.agent is not None,
    }


@app.get("/")
async def root():
    """API info."""
    return {
        "name": "Ayaan's Gmail Autoresponder Agent",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "get_auth_url": "GET /auth/url",
                "submit_code": "POST /auth/callback",
                "token_status": "GET /auth/status",
                "refresh_token": "POST /auth/refresh",
                "delete_token": "DELETE /auth/token",
            },
            "emails": {
                "list": "POST /emails/list",
                "read": "POST /emails/read",
                "regenerate_draft": "POST /emails/regenerate-draft",
                "reply": "POST /emails/reply",
            },
            "agent": {
                "chat": "POST /agent/chat",
                "reset": "POST /agent/reset",
            },
            "monitoring": {
                "metrics": "GET /metrics",
                "workflow_diagram": "GET /workflow-diagram",
            }
        }
    }


# =========================
# Metrics & Monitoring Endpoints
# =========================
@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics() -> Response:
    """
    Get Prometheus-compatible metrics for the agent and system.
    
    This endpoint exposes comprehensive metrics including:
    - API request counts and durations
    - Gmail operation metrics
    - Authentication status
    - Agent/AI chat metrics
    - Ollama LLM request metrics
    - Error counts
    - Resource usage
    
    Returns:
        Prometheus-formatted metrics text
    """
    try:
        # Update token status in metrics
        token_status = check_token_status()
        metrics_collector.set_token_status(token_status.get("valid", False))
        
        # Generate current metrics
        metrics_output = get_metrics_output()
        
        # Return as Prometheus text format
        return Response(
            content=metrics_output,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate metrics: {str(e)}"
        )


@app.get("/workflow-diagram", response_class=HTMLResponse)
async def get_workflow_diagram() -> HTMLResponse:
    """
    Get an interactive HTML diagram of the workflow.
    
    Shows:
    - Authentication flow (OAuth)
    - Agent chat processing
    - Tool execution (list_emails, read_email, send_email_reply)
    - Gmail API integration
    - LLM processing with Ollama
    
    Returns:
        Interactive HTML page with workflow diagram
    """
    try:
        html_content = generate_html_diagram()
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workflow diagram: {str(e)}"
        )


@app.get("/config")
async def get_configuration() -> Dict[str, Any]:
    """
    Get current system configuration.
    
    Returns:
        System configuration (non-sensitive values only)
    """
    from app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
    
    return {
        "app_name": "Ayaan's Gmail Autoresponder Agent",
        "version": "1.0.0",
        "ollama": {
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "connected": state.ollama_client is not None
        },
        "gmail": {
            "authenticated": state.gmail_service is not None,
            "token_valid": check_token_status().get("valid", False)
        },
        "agent": {
            "ready": state.agent is not None,
            "tools": ["list_emails", "read_email", "send_email_reply"]
        }
    }


# =========================
# OAuth Authentication Endpoints
# =========================
@app.get("/auth/url", response_model=AuthUrlResponse)
async def get_auth_url(
    redirect_uri: str = Query(
        default="urn:ietf:wg:oauth:2.0:oob",
        description="Redirect URI. Use 'urn:ietf:wg:oauth:2.0:oob' for manual code entry"
    )
):
    """
    Generate Gmail OAuth authorization URL.
    
    Steps:
    1. Call this endpoint to get the authorization URL
    2. Open the URL in a browser and authorize
    3. Copy the authorization code
    4. Submit the code to POST /auth/callback
    """
    try:
        auth_url, flow = generate_auth_url(redirect_uri)
        # Store flow for potential callback use
        state.oauth_flow = flow
        
        metrics_collector.record_auth_operation("get_url", "success")
        
        return AuthUrlResponse(
            auth_url=auth_url,
            redirect_uri=redirect_uri,
            instructions=(
                "1. Open the auth_url in a browser\n"
                "2. Sign in and authorize the application\n"
                "3. Copy the authorization code\n"
                "4. POST to /auth/callback with the code"
            )
        )
    except Exception as e:
        metrics_collector.record_auth_operation("get_url", "error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/callback")
async def auth_callback(request: AuthCallbackRequest):
    """
    Exchange authorization code for access token.
    
    Submit the authorization code received from Google after authorization.
    This creates the token.json file and initializes the Gmail service.
    """
    try:
        token_data = create_token_from_code(
            authorization_code=request.code,
            redirect_uri=request.redirect_uri
        )
        
        # Reinitialize Gmail service with new token
        state.gmail_service = get_gmail_service(force_refresh=True)
        
        # Test connection to get email
        success, message = test_gmail_connection(state.gmail_service)
        
        # Reinitialize agent if possible
        if state.gmail_service and state.ollama_client:
            state.mailbox = MailboxSession()
            state.agent = GmailAgent(
                ollama_client=state.ollama_client,
                gmail_service=state.gmail_service,
                mailbox=state.mailbox
            )
        
        metrics_collector.record_auth_operation("callback", "success")
        metrics_collector.set_token_status(True)
        
        return {
            "success": True,
            "message": "Token created successfully",
            "gmail_connected": success,
            "gmail_status": message,
            "token_expiry": token_data.get("expiry")
        }
    except Exception as e:
        metrics_collector.record_auth_operation("callback", "error")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/status", response_model=TokenStatusResponse)
async def get_token_status():
    """
    Check the status of the current OAuth token.
    """
    status = check_token_status()
    
    # Update metrics
    metrics_collector.set_token_status(status.get("valid", False))
    
    # Try to get email if token is valid
    email = None
    if status.get("valid") and state.gmail_service:
        try:
            profile = state.gmail_service.users().getProfile(userId="me").execute()
            email = profile.get("emailAddress")
        except:
            pass
    
    return TokenStatusResponse(
        exists=status.get("exists", False),
        valid=status.get("valid", False),
        expired=status.get("expired"),
        has_refresh_token=status.get("has_refresh_token"),
        expiry=status.get("expiry"),
        email=email,
        message=status.get("message", "")
    )


@app.post("/auth/refresh")
async def refresh_auth_token():
    """
    Manually refresh the OAuth token.
    
    Tokens are automatically refreshed when needed, but this endpoint
    allows manual refresh if desired.
    """
    result = refresh_token()
    
    if result.get("success"):
        metrics_collector.record_auth_operation("refresh", "success")
        # Reinitialize service with refreshed token
        try:
            state.gmail_service = get_gmail_service(force_refresh=True)
        except:
            pass
    else:
        metrics_collector.record_auth_operation("refresh", "error")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.delete("/auth/token")
async def delete_auth_token():
    """
    Delete the current OAuth token.
    
    Use this to force re-authorization. After deleting, you'll need to
    go through the OAuth flow again using /auth/url.
    """
    result = delete_token()
    
    # Clear Gmail service
    state.gmail_service = None
    state.agent = None
    
    metrics_collector.record_auth_operation("delete", "success")
    metrics_collector.set_token_status(False)
    
    return result


# =========================
# Email Endpoints
# =========================
def ensure_gmail_service():
    """Ensure Gmail service is available."""
    if not state.gmail_service:
        token_status = check_token_status()
        if not token_status.get("valid"):
            raise HTTPException(
                status_code=401,
                detail="Gmail not authenticated. Use /auth/url to get authorization URL."
            )
        try:
            state.gmail_service = get_gmail_service()
            # Reinitialize mailbox and agent
            state.mailbox = MailboxSession()
            if state.ollama_client:
                state.agent = GmailAgent(
                    ollama_client=state.ollama_client,
                    gmail_service=state.gmail_service,
                    mailbox=state.mailbox
                )
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/emails/list")
async def list_emails(request: ListEmailsRequest):
    """List emails from Gmail inbox."""
    ensure_gmail_service()
    
    result = state.mailbox.list_emails(
        state.gmail_service,
        max_results=request.max_results,
        query=request.query
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Record metrics
    if "emails" in result:
        metrics_collector.record_email_listed(len(result["emails"]))
    
    return result


@app.post("/emails/read")
async def read_email(request: ReadEmailRequest):
    """Read an email and optionally generate a draft reply."""
    ensure_gmail_service()
    
    # Validate tone
    valid_tones = ["normal", "friendly", "professional"]
    tone = request.tone if request.tone in valid_tones else "normal"
    
    result = state.mailbox.read_email(
        state.gmail_service,
        number=request.email_number,
        generate_draft=request.generate_draft,
        tone=tone
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Record metrics
    metrics_collector.record_email_read()
    if request.generate_draft and "draft_reply" in result:
        metrics_collector.record_draft_generated()
    
    return result


@app.post("/emails/regenerate-draft")
async def regenerate_draft(request: RegenerateDraftRequest):
    """
    Regenerate a draft reply with a specific tone.
    
    Tones available:
    - normal: Balanced, straightforward (default) - Signature: Regards, Ayaan
    - friendly: Warm, casual, approachable - Signature: Regards, Ayaan
    - professional: Formal, official correspondence - Signature: Regards, Ayaan Asish, Grade 11, West Carleton Secondary School, Ontario
    """
    ensure_gmail_service()
    
    # Validate tone
    valid_tones = ["normal", "friendly", "professional"]
    if request.tone not in valid_tones:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tone '{request.tone}'. Valid options: {', '.join(valid_tones)}"
        )
    
    result = state.mailbox.regenerate_draft(
        number=request.email_number,
        tone=request.tone
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Record metrics
    metrics_collector.record_draft_generated()
    
    return result


@app.post("/emails/reply")
async def send_reply(request: SendReplyRequest):
    """Send a reply to an email."""
    ensure_gmail_service()
    
    result = state.mailbox.send_reply(
        state.gmail_service,
        number=request.email_number,
        reply_body=request.reply_body
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Record metrics
    metrics_collector.record_email_sent()
    
    return result


# =========================
# Agent Endpoints
# =========================
@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """Chat with Ayaan's Gmail agent."""
    import time
    
    ensure_gmail_service()
    
    if not state.agent:
        if not state.ollama_client:
            raise HTTPException(
                status_code=503,
                detail="Ollama client not available. Check Ollama configuration."
            )
        # Try to initialize agent
        state.agent = GmailAgent(
            ollama_client=state.ollama_client,
            gmail_service=state.gmail_service,
            mailbox=state.mailbox
        )
    
    start_time = time.time()
    try:
        response = state.agent.chat(request.message)
        duration = time.time() - start_time
        conversation_length = len(state.agent.conversation_history)
        
        # Record metrics
        metrics_collector.record_agent_chat("success", duration, conversation_length)
        
        return ChatResponse(
            response=response,
            conversation_length=conversation_length
        )
    except Exception as e:
        duration = time.time() - start_time
        metrics_collector.record_agent_chat("error", duration, 0)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/reset")
async def agent_reset():
    """Reset the agent conversation."""
    if state.agent:
        state.agent.reset()
    if state.mailbox:
        state.mailbox.clear()
    
    return {"status": "reset", "message": "Agent and mailbox session cleared"}


# =========================
# CLI Mode
# =========================
def run_cli():
    """Run interactive CLI mode for testing."""
    print("🧪 Ayaan's Gmail Agent - CLI Mode")
    print("=" * 50)
    
    # Check token status
    token_status = check_token_status()
    if not token_status.get("valid"):
        print(f"⚠️  Token status: {token_status.get('message')}")
        print("\nStarting OAuth flow...")
        
        # Generate auth URL
        auth_url, flow = generate_auth_url()
        print(f"\n🔗 Open this URL in your browser:\n{auth_url}\n")
        
        # Get code from user
        code = input("Enter the authorization code: ").strip()
        
        try:
            from app.clients.gmail_client import exchange_code_for_token
            exchange_code_for_token(flow, code)
            print("✅ Token created successfully!")
        except Exception as e:
            print(f"❌ Failed to create token: {e}")
            return
    
    # Initialize services
    try:
        gmail_service = get_gmail_service()
        success, msg = test_gmail_connection(gmail_service)
        print(f"✅ Gmail: {msg}")
    except Exception as e:
        print(f"❌ Gmail failed: {e}")
        return
    
    try:
        ollama_client = get_ollama_client()
        success, msg = ollama_client.test_connection()
        print(f"{'✅' if success else '⚠️'} Ollama: {msg[:50]}...")
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
        return
    
    # Create agent
    mailbox = MailboxSession()
    agent = GmailAgent(ollama_client, gmail_service, mailbox)
    
    print("\n💬 Type your message (or 'quit' to exit, 'reset' to clear history)")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("👋 Goodbye from Ayaan's Gmail Agent!")
                break
            if user_input.lower() == "reset":
                agent.reset()
                print("🔄 Conversation reset")
                continue
            
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye from Ayaan's Gmail Agent!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        run_cli()
    else:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
