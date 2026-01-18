#!/bin/bash
# ===========================================
# Ayaan's Gmail Autoresponder Agent - Personal Config
# ===========================================
# DO NOT COMMIT THIS FILE TO GIT!

set -e

echo "Loading Ayaan's personal credentials..."

# Create .env
cat > .env << 'EOF'
# Ayaan's Gmail Autoresponder Agent Configuration

# Ollama API
OLLAMA_API_KEY=fd50dc7dd34942f9980d68d328976044.TDRUngN4XGJhe6yuTkX9yNdJ
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=ministral-3:8b-cloud

# Gmail OAuth
GMAIL_CLIENT_ID=30656517490-lkvtr9hof7t9bf0tq035f7sq7ak2uuv3.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=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
EOF
echo "✓ .env created"

# Create credentials.json
cat > app/credentials.json << 'EOF'
{"installed":{"client_id":"30656517490-lkvtr9hof7t9bf0tq035f7sq7ak2uuv3.apps.googleusercontent.com","project_id":"gmailagent-482201","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}
EOF
echo "✓ app/credentials.json created"

echo ""
echo "Ayaan's credentials loaded successfully!"
echo ""
echo "Next: Restart server and use /auth/url API to generate token"
