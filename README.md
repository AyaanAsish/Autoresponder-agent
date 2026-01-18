# 📧 Ayaan's Gmail Autoresponder Agent

An AI-powered Gmail assistant built with FastAPI and Ollama Cloud. Features a web UI for easy email management with AI-generated draft replies.

## ✨ Features

- **🌐 Web UI** - Beautiful interface to manage emails
- **🔐 OAuth via UI/API** - Easy Gmail authentication
- **📬 List Emails** - Search and browse emails
- **📖 Read Emails** - View content with AI-generated drafts
- **✉️ Send Replies** - Review and send AI-drafted responses
- **🤖 AI Agent** - Natural language email management
- **📊 Prometheus Metrics** - Monitor agent performance
- **📈 Workflow Diagram** - Interactive visualization of the system
- **🐳 Docker Support** - One-command deployment

## 🚀 Quick Start

```bash
# 1. Load credentials
make setup-personal

# 2. Build and start (API + UI)
make docker-up

# 3. Open UI
open http://localhost:3000
```

That's it! Use the web UI to authenticate Gmail and manage emails.

---

## 📁 Project Structure

```
Autoresponder-agent/
├── app/                     # Backend API
│   ├── main.py              # FastAPI entry point
│   ├── core/                # Configuration
│   ├── clients/             # Gmail & Ollama clients
│   ├── utils/               # Helper functions
│   │   ├── metrics.py       # Prometheus metrics
│   │   ├── diagram_generator.py  # Workflow diagrams
│   │   └── ...
│   └── agents/              # AI agent
├── ui/                      # Frontend UI
│   ├── index.html           # Main UI page (with metrics/workflow tabs)
│   ├── config.js            # API configuration
│   ├── nginx.conf           # Nginx config
│   └── Dockerfile           # UI container
├── scripts/                 # Setup scripts
├── docker-compose.yml       # Multi-container setup
├── Dockerfile               # API container
├── Makefile
└── README.md
```

---

## 🌐 Web UI

The web UI provides:

- **📬 Emails Tab** - Main email management interface
  - Authentication Panel - Connect/disconnect Gmail
  - Email List - Browse and search emails
  - Email Detail - Read full email content
  - Draft Editor - Review and edit AI-generated replies
  - Send Button - Send replies with one click
  
- **📈 Workflow Diagram Tab** - Interactive visualization
  - System architecture overview
  - Data flow between components
  - Agent tool execution flow
  
- **📊 Metrics Tab** - Prometheus metrics dashboard
  - Emails read/sent counters
  - Draft replies generated
  - Chat requests processed
  - Raw Prometheus metrics output

---

## 🐳 Docker Deployment

### Start Everything

```bash
# Load credentials + build + start
make docker-personal

# Or step by step:
make setup-personal
make docker-build
make docker-up
```

### Access Points

| Service | URL |
|---------|-----|
| **Web UI** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Metrics** | http://localhost:8000/metrics |
| **Workflow Diagram** | http://localhost:8000/workflow-diagram |

### Docker Commands

```bash
make docker-up        # Start all
make docker-down      # Stop all
make docker-logs      # View all logs
make docker-logs-api  # API logs only
make docker-logs-ui   # UI logs only
make docker-restart   # Restart all
make docker-clean     # Remove everything
```

---

## 🔐 Authentication

### Via Web UI (Recommended)

1. Open http://localhost:3000
2. Click **"Connect Gmail"**
3. Click **"Get Auth URL"** - opens Google auth page
4. Authorize and copy the code
5. Paste code and click **"Submit Code"**
6. Done! Start managing emails

### Via API

```bash
# Get auth URL
curl http://localhost:8000/auth/url

# Submit code
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_CODE"}'

# Check status
curl http://localhost:8000/auth/status
```

---

## 📡 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/url` | GET | Get OAuth URL |
| `/auth/callback` | POST | Submit auth code |
| `/auth/status` | GET | Token status |
| `/auth/refresh` | POST | Refresh token |
| `/auth/token` | DELETE | Delete token |

### Emails
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/emails/list` | POST | List emails |
| `/emails/read` | POST | Read + generate draft |
| `/emails/reply` | POST | Send reply |

### Agent
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/chat` | POST | Chat with agent |
| `/agent/reset` | POST | Reset conversation |

### Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/metrics` | GET | Prometheus metrics |
| `/workflow-diagram` | GET | Interactive workflow diagram |
| `/config` | GET | System configuration |
| `/health` | GET | Health check |

---

## 📊 Prometheus Metrics

The agent exposes comprehensive Prometheus metrics at `/metrics`:

### Gmail Operations
- `gmail_agent_emails_read_total` - Total emails read
- `gmail_agent_emails_sent_total` - Total emails/replies sent
- `gmail_agent_draft_replies_generated_total` - AI drafts generated
- `gmail_agent_gmail_operations_total` - All Gmail operations by type

### Agent/AI Metrics
- `gmail_agent_chat_requests_total` - Chat requests by status
- `gmail_agent_chat_duration_seconds` - Chat processing time
- `gmail_agent_tool_calls_total` - Tool calls by function name
- `gmail_agent_conversation_length` - Conversation history size

### Authentication
- `gmail_agent_auth_operations_total` - Auth operations by type
- `gmail_agent_token_valid` - Token validity status (0/1)

### LLM/Ollama
- `gmail_agent_ollama_requests_total` - Ollama requests by model
- `gmail_agent_ollama_request_duration_seconds` - Request latency
- `gmail_agent_ollama_connected` - Connection status (0/1)

### System
- `gmail_agent_api_requests_total` - API requests by endpoint
- `gmail_agent_api_request_duration_seconds` - API latency
- `gmail_agent_errors_total` - Errors by component
- `gmail_agent_memory_usage_bytes` - Memory usage

---

## 📈 Workflow Diagram

The `/workflow-diagram` endpoint provides an interactive HTML visualization showing:

1. **Authentication Flow** - OAuth process with Google
2. **Agent Chat Flow** - How natural language is processed
3. **Tool Execution** - How list_emails, read_email, send_email_reply work
4. **Gmail API Integration** - Connection to Google services
5. **LLM Processing** - Ollama model interaction

Access via:
- Direct URL: http://localhost:8000/workflow-diagram
- Web UI: Click the **"📈 Workflow Diagram"** tab

---

## 🛠️ Makefile Commands

### Quick Start
| Command | Description |
|---------|-------------|
| `make docker-personal` | Setup + build + start all |
| `make docker-up` | Start API + UI |
| `make docker-down` | Stop all |
| `make open` | Open UI in browser |

### Development
| Command | Description |
|---------|-------------|
| `make run` | Start API locally |
| `make run-dev` | Start with auto-reload |
| `make cli` | Interactive CLI |

### Status
| Command | Description |
|---------|-------------|
| `make status` | Show all status |
| `make health` | Check API health |
| `make info` | Show endpoints |

---

## 🔧 Configuration

### Environment Variables (.env)

| Variable | Description |
|----------|-------------|
| `OLLAMA_API_KEY` | Ollama Cloud API key |
| `OLLAMA_BASE_URL` | Ollama endpoint |
| `OLLAMA_MODEL` | Model name |
| `GMAIL_CLIENT_ID` | Google OAuth Client ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth Secret |

### Files

| File | Purpose | Git Status |
|------|---------|------------|
| `.env` | API keys | Ignored |
| `app/credentials.json` | OAuth client | Ignored |
| `token.json` | OAuth token | Ignored |

---

## 🐛 Troubleshooting

### UI can't connect to API
- Check both containers are running: `make status`
- Check logs: `make docker-logs`

### Authentication fails
- Verify credentials match in `.env` and `credentials.json`
- Try: `make docker-down && make setup-personal && make docker-up`

### Token issues
- Delete and re-authenticate via UI
- Or: `curl -X DELETE http://localhost:8000/auth/token`

### Check everything
```bash
make status
```

---

## 📄 License

MIT License

---

**Built with ❤️ for Ayaan**
