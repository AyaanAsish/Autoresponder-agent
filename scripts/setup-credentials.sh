#!/bin/bash
# ===========================================
# Ayaan's Gmail Autoresponder Agent - Credentials Setup
# ===========================================
# This script creates the credentials.json file for Gmail OAuth
# Run: ./scripts/setup-credentials.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CREDS_FILE="app/credentials.json"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Ayaan's Gmail Agent - OAuth Credentials Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if credentials.json already exists
if [ -f "$CREDS_FILE" ]; then
    echo -e "${YELLOW}⚠ credentials.json already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Keeping existing credentials.json${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}Gmail OAuth2 Credentials${NC}"
echo ""
echo "Get these from Google Cloud Console:"
echo -e "  ${BLUE}https://console.cloud.google.com/apis/credentials${NC}"
echo ""
echo "Steps:"
echo "  1. Create a new project or select existing"
echo "  2. Enable the Gmail API"
echo "  3. Create OAuth 2.0 Client ID (Desktop app)"
echo "  4. Copy the Client ID and Client Secret"
echo ""

read -p "Enter Client ID: " CLIENT_ID
read -p "Enter Client Secret: " CLIENT_SECRET
read -p "Enter Project ID [ayaan-gmail-agent]: " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-ayaan-gmail-agent}

# Create credentials.json
cat > "$CREDS_FILE" << EOF
{
  "installed": {
    "client_id": "${CLIENT_ID}",
    "project_id": "${PROJECT_ID}",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "${CLIENT_SECRET}",
    "redirect_uris": ["http://localhost"]
  }
}
EOF

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ credentials.json created successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Run: make run     (start the server)"
echo "  2. Use /auth/url API to authenticate Gmail"
echo ""
