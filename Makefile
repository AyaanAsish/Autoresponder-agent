# Ayaan's Gmail Autoresponder Agent Build Configuration
IMAGE_NAME := ayaan-gmail-agent
UI_IMAGE_NAME := ayaan-gmail-ui
CONTAINER_NAME := ayaan-gmail-agent
UI_CONTAINER_NAME := ayaan-gmail-ui
API_PORT := 8000
UI_PORT := 3000

# Detect docker compose command (v2 uses 'docker compose', v1 uses 'docker-compose')
DOCKER_COMPOSE := $(shell docker compose version > /dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

# Colors for output
GREEN := \033[32m
BLUE := \033[34m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Detect if already in virtual environment
INVENV := $(shell python -c 'import sys; print("1" if sys.prefix != sys.base_prefix else "0")' 2>/dev/null || echo "0")

# Default target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(BLUE)    Ayaan's Gmail Autoresponder Agent Build System$(RESET)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  make setup-personal  # Load saved credentials"
	@echo "  make docker-build    # Build images"
	@echo "  make docker-up       # Start containers"
	@echo "  Open http://localhost:$(UI_PORT) for UI"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ============================================================
# Setup & Installation
# ============================================================
.PHONY: setup setup-full setup-personal install setup-env setup-credentials check-env

setup: check-env install setup-env-copy ## Quick setup (copy .env.example)
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(GREEN)Setup completed!$(RESET)"
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. make setup-env         (configure API keys)"
	@echo "  2. make setup-credentials (configure Gmail OAuth)"
	@echo "  3. make docker-build      (build images)"
	@echo "  4. make docker-up         (start containers)"
	@echo "  5. Open http://localhost:$(UI_PORT) to authenticate"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"

setup-full: check-env install setup-env setup-credentials ## Full interactive setup
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(GREEN)Full setup completed!$(RESET)"
	@echo "$(YELLOW)Next: make docker-build && make docker-up$(RESET)"
	@echo "$(YELLOW)Then open http://localhost:$(UI_PORT)$(RESET)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"

setup-personal: ## Load saved credentials (.env + credentials.json)
	@if [ -f scripts/setup-personal.sh ]; then \
		chmod +x scripts/setup-personal.sh; \
		bash scripts/setup-personal.sh; \
	else \
		echo "$(RED)Error: scripts/setup-personal.sh not found$(RESET)"; \
		echo "$(YELLOW)Copy from template: cp scripts/setup-personal.sh.template scripts/setup-personal.sh$(RESET)"; \
		exit 1; \
	fi

check-env: ## Check Python environment
	@echo "$(BLUE)Checking Python environment...$(RESET)"
ifeq ($(INVENV),1)
	@echo "$(GREEN)✓ Already in virtual environment$(RESET)"
else
	@echo "$(YELLOW)⚠ Not in a virtual environment$(RESET)"
	@echo "$(YELLOW)  Consider: conda activate <env> or source venv/bin/activate$(RESET)"
endif
	@python --version

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(RESET)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing dev dependencies...$(RESET)"
	pip install pytest pytest-asyncio httpx black flake8
	@echo "$(GREEN)Dev dependencies installed!$(RESET)"

setup-env: ## Configure .env interactively
	@chmod +x scripts/setup-env.sh 2>/dev/null || true
	@bash scripts/setup-env.sh

setup-credentials: ## Configure Gmail credentials.json interactively
	@chmod +x scripts/setup-credentials.sh 2>/dev/null || true
	@bash scripts/setup-credentials.sh

setup-env-copy: ## Copy .env.example to .env
	@if [ ! -f .env ] || [ ! -s .env ] || grep -q "^OLLAMA_API_KEY=$$" .env 2>/dev/null; then \
		cp .env.example .env; \
		echo "$(GREEN).env created$(RESET)"; \
	else \
		echo "$(YELLOW).env already configured$(RESET)"; \
	fi

# ============================================================
# Running the Application
# ============================================================
.PHONY: run run-dev cli auth

run: ## Start the FastAPI server
	@echo "$(BLUE)Starting Ayaan's Gmail Autoresponder Agent...$(RESET)"
	@echo "$(YELLOW)API:  http://localhost:$(API_PORT)$(RESET)"
	@echo "$(YELLOW)Docs: http://localhost:$(API_PORT)/docs$(RESET)"
	@echo ""
	uvicorn app.main:app --host 0.0.0.0 --port $(API_PORT)

run-dev: ## Start with auto-reload (development)
	uvicorn app.main:app --host 0.0.0.0 --port $(API_PORT) --reload

cli: ## Run interactive CLI mode
	python -m app.main cli

auth: ## Generate OAuth token via CLI (opens browser)
	@echo "$(BLUE)Starting Gmail OAuth (CLI mode)...$(RESET)"
	python -m app.main cli

# ============================================================
# Docker Commands
# ============================================================
.PHONY: docker-build docker-build-api docker-build-ui docker-up docker-down docker-logs docker-shell docker-clean docker-restart docker-start docker-personal

docker-build: docker-build-api docker-build-ui ## Build all Docker images
	@echo "$(GREEN)All images built!$(RESET)"

docker-build-api: ## Build API Docker image
	@echo "$(BLUE)Building API image...$(RESET)"
	docker build -t $(IMAGE_NAME):latest .
	@echo "$(GREEN)API image built: $(IMAGE_NAME):latest$(RESET)"

docker-build-ui: ## Build UI Docker image
	@echo "$(BLUE)Building UI image...$(RESET)"
	docker build -t $(UI_IMAGE_NAME):latest ./ui
	@echo "$(GREEN)UI image built: $(UI_IMAGE_NAME):latest$(RESET)"

docker-up: ## Start containers (API + UI) - no build
	@echo "$(BLUE)Starting Ayaan's Gmail Agent (API + UI)...$(RESET)"
	@# Create empty token.json if not exists to prevent directory mount
	@touch token.json 2>/dev/null || true
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(GREEN)✓ Ayaan's Gmail Agent is running!$(RESET)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)🌐 UI:   http://localhost:$(UI_PORT)$(RESET)"
	@echo "$(YELLOW)🔌 API:  http://localhost:$(API_PORT)$(RESET)"
	@echo "$(YELLOW)📖 Docs: http://localhost:$(API_PORT)/docs$(RESET)"
	@echo ""

docker-start: docker-build docker-up ## Build and start all containers

docker-down: ## Stop Docker Compose
	@echo "$(BLUE)Stopping containers...$(RESET)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Stopped!$(RESET)"

docker-restart: docker-down docker-up ## Restart containers (no rebuild)

docker-rebuild: docker-down docker-build docker-up ## Rebuild and restart all

docker-logs: ## View all container logs
	$(DOCKER_COMPOSE) logs -f

docker-logs-api: ## View API logs only
	$(DOCKER_COMPOSE) logs -f $(CONTAINER_NAME)

docker-logs-ui: ## View UI logs only
	$(DOCKER_COMPOSE) logs -f $(UI_CONTAINER_NAME)

docker-shell: ## Shell into API container
	docker exec -it $(CONTAINER_NAME) /bin/bash

docker-shell-ui: ## Shell into UI container
	docker exec -it $(UI_CONTAINER_NAME) /bin/sh

docker-personal: setup-personal docker-build docker-up ## Load credentials + build + start all
	@echo ""
	@echo "$(GREEN)Use the UI to authenticate Gmail: http://localhost:$(UI_PORT)$(RESET)"

docker-clean: ## Remove images and containers
	$(DOCKER_COMPOSE) down --rmi local -v 2>/dev/null || true
	docker rmi $(IMAGE_NAME):latest 2>/dev/null || true
	docker rmi $(UI_IMAGE_NAME):latest 2>/dev/null || true
	@echo "$(GREEN)Cleaned!$(RESET)"

# ============================================================
# Health & Status
# ============================================================
.PHONY: health status test-api test-list test-chat test-auth

health: ## Check API health
	@curl -sf http://localhost:$(API_PORT)/health | python -m json.tool 2>/dev/null \
		|| echo "$(RED)API not responding$(RESET)"

status: ## Show detailed status
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(BLUE)Ayaan's Gmail Autoresponder Agent Status$(RESET)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)Configuration:$(RESET)"
	@if [ -f .env ] && ! grep -q "^OLLAMA_API_KEY=$$" .env 2>/dev/null; then \
		echo "  $(GREEN)✓$(RESET) .env"; \
	else \
		echo "  $(RED)✗$(RESET) .env (run: make setup-env)"; \
	fi
	@if [ -f app/credentials.json ]; then \
		echo "  $(GREEN)✓$(RESET) credentials.json"; \
	else \
		echo "  $(RED)✗$(RESET) credentials.json (run: make setup-credentials)"; \
	fi
	@if [ -f token.json ] && [ -s token.json ]; then \
		echo "  $(GREEN)✓$(RESET) token.json"; \
	else \
		echo "  $(YELLOW)○$(RESET) token.json (authenticate via UI)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Docker Images:$(RESET)"
	@docker images $(IMAGE_NAME):latest --format "  $(GREEN)✓$(RESET) $(IMAGE_NAME):latest" 2>/dev/null || echo "  $(RED)✗$(RESET) $(IMAGE_NAME) (run: make docker-build-api)"
	@docker images $(UI_IMAGE_NAME):latest --format "  $(GREEN)✓$(RESET) $(UI_IMAGE_NAME):latest" 2>/dev/null || echo "  $(RED)✗$(RESET) $(UI_IMAGE_NAME) (run: make docker-build-ui)"
	@echo ""
	@echo "$(YELLOW)Services:$(RESET)"
	@curl -sf http://localhost:$(API_PORT)/health > /dev/null 2>&1 \
		&& echo "  $(GREEN)✓$(RESET) API running at http://localhost:$(API_PORT)" \
		|| echo "  $(RED)✗$(RESET) API not running"
	@curl -sf http://localhost:$(UI_PORT)/health > /dev/null 2>&1 \
		&& echo "  $(GREEN)✓$(RESET) UI running at http://localhost:$(UI_PORT)" \
		|| echo "  $(RED)✗$(RESET) UI not running"
	@curl -sf http://localhost:$(API_PORT)/auth/status 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(f'  Gmail: {d.get(\"email\",\"not connected\")}' if d.get('valid') else '  Gmail: not authenticated')" 2>/dev/null || true

test-auth: ## Test auth status endpoint
	@curl -sf http://localhost:$(API_PORT)/auth/status | python -m json.tool 2>/dev/null \
		|| echo "$(RED)API not responding$(RESET)"

test-list: ## Test list emails
	@curl -sf -X POST http://localhost:$(API_PORT)/emails/list \
		-H "Content-Type: application/json" \
		-d '{"max_results": 5, "query": "is:unread"}' \
		| python -m json.tool 2>/dev/null \
		|| echo "$(RED)Failed$(RESET)"

test-chat: ## Test agent chat
	@curl -sf -X POST http://localhost:$(API_PORT)/agent/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "Show me my recent emails"}' \
		| python -m json.tool 2>/dev/null \
		|| echo "$(RED)Failed$(RESET)"

# ============================================================
# Development
# ============================================================
.PHONY: test lint format

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	flake8 app/ --max-line-length=100 --extend-ignore=E203,W503

format: ## Format code
	black app/

# ============================================================
# Cleanup
# ============================================================
.PHONY: clean clean-all clean-pycache clean-secrets

clean: clean-pycache ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov

clean-pycache: ## Clean Python cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean ## Clean everything including venv
	rm -rf venv/ .venv/

clean-secrets: ## Remove credential files
	rm -f .env token.json app/credentials.json
	@echo "$(GREEN)Credentials removed$(RESET)"

clean-docker: docker-clean ## Alias

# ============================================================
# Utility
# ============================================================
.PHONY: logs info open

logs: docker-logs ## Alias for docker-logs

open: ## Open UI in browser
	@echo "$(BLUE)Opening UI in browser...$(RESET)"
	@which xdg-open > /dev/null 2>&1 && xdg-open http://localhost:$(UI_PORT) || \
	which open > /dev/null 2>&1 && open http://localhost:$(UI_PORT) || \
	echo "$(YELLOW)Open http://localhost:$(UI_PORT) in your browser$(RESET)"

info: ## Show API endpoints
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(BLUE)Ayaan's Gmail Autoresponder Agent - Endpoints$(RESET)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)UI:$(RESET)"
	@echo "  http://localhost:$(UI_PORT)"
	@echo ""
	@echo "$(YELLOW)Authentication:$(RESET)"
	@echo "  GET  /auth/url       Get OAuth URL"
	@echo "  POST /auth/callback  Submit auth code"
	@echo "  GET  /auth/status    Token status"
	@echo "  POST /auth/refresh   Refresh token"
	@echo "  DEL  /auth/token     Delete token"
	@echo ""
	@echo "$(YELLOW)Emails:$(RESET)"
	@echo "  POST /emails/list    List emails"
	@echo "  POST /emails/read    Read + draft"
	@echo "  POST /emails/reply   Send reply"
	@echo ""
	@echo "$(YELLOW)Agent:$(RESET)"
	@echo "  POST /agent/chat     Chat"
	@echo "  POST /agent/reset    Reset"
	@echo ""
	@echo "$(YELLOW)API Docs: http://localhost:$(API_PORT)/docs$(RESET)"
