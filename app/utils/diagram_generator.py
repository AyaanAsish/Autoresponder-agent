"""
Ayaan's Gmail Autoresponder Agent Workflow Diagram Generator

Generates visual representations of the email processing workflow
through the agent system.
"""


def generate_ascii_diagram():
    """Generate ASCII art diagram of the Gmail Autoresponder workflow."""
    return """
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║            Ayaan's GMAIL AUTORESPONDER AGENT - WORKFLOW DIAGRAM                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝

┌──────────┐
│   USER   │ ◄─────────────────────────────────────────────────────────────┐
└────┬─────┘                                                               │
     │ Natural Language Request                                            │ Response / Draft Reply
     ▼                                                                     │
═══════════════════════════════════════════════════════════════════════════▼═══════════════
                              FASTAPI APPLICATION
═══════════════════════════════════════════════════════════════════════════════════════════
     │
     ├───────────────────────────────────────────────────────────────────────────────────┐
     │                                                                                   │
     ▼                                                                                   ▼
┌─────────────────────────────────────┐          ┌─────────────────────────────────────────┐
│        AUTHENTICATION FLOW          │          │           AGENT CHAT FLOW               │
│                                     │          │                                         │
│  ┌───────────────────────────────┐  │          │  ┌───────────────────────────────────┐  │
│  │  GET /auth/url                │  │          │  │  POST /agent/chat                 │  │
│  │  → Generate OAuth URL         │  │          │  │  → Natural language interface     │  │
│  └─────────────┬─────────────────┘  │          │  └─────────────┬─────────────────────┘  │
│                │                    │          │                │                        │
│                ▼                    │          │                ▼                        │
│  ┌───────────────────────────────┐  │          │  ┌───────────────────────────────────┐  │
│  │  User opens URL in browser    │  │          │  │        GMAIL AGENT                │  │
│  │  → Google OAuth consent       │  │          │  │                                   │  │
│  └─────────────┬─────────────────┘  │          │  │  ┌─────────────────────────────┐  │  │
│                │                    │          │  │  │  System Prompt              │  │  │
│                ▼                    │          │  │  │  + Conversation History     │  │  │
│  ┌───────────────────────────────┐  │          │  │  │  + User Message             │  │  │
│  │  POST /auth/callback          │  │          │  │  └─────────────┬───────────────┘  │  │
│  │  → Exchange code for token    │  │          │  │                │                  │  │
│  │  → Create token.json          │  │          │  │                ▼                  │  │
│  └─────────────┬─────────────────┘  │          │  │  ╔═══════════════════════════╗   │  │
│                │                    │          │  │  ║   OLLAMA LLM (Cloud)      ║   │  │
│                ▼                    │          │  │  ║   Model: llama3.2/qwen2.5 ║   │  │
│  ┌───────────────────────────────┐  │          │  │  ║   with Tool Calling       ║   │  │
│  │  Gmail Service Initialized    │  │          │  │  ╚═══════════╤═══════════════╝   │  │
│  │  → Ready for operations       │  │          │  │              │                   │  │
│  └───────────────────────────────┘  │          │  │              ▼                   │  │
└─────────────────────────────────────┘          │  │  ┌─────────────────────────┐     │  │
                                                 │  │  │   Tool Call Decision    │     │  │
                                                 │  │  │   ┌─────────────────┐   │     │  │
                                                 │  │  │   │ list_emails     │   │     │  │
                                                 │  │  │   │ read_email      │   │     │  │
                                                 │  │  │   │ send_email_reply│   │     │  │
                                                 │  │  │   └─────────────────┘   │     │  │
                                                 │  │  └───────────┬─────────────┘     │  │
                                                 │  │              │                   │  │
                                                 │  └──────────────┼───────────────────┘  │
                                                 │                 │                      │
                                                 └─────────────────┼──────────────────────┘
                                                                   │
                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL EXECUTION LAYER                                        │
│                                                                                          │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐         │
│  │    list_emails        │  │     read_email        │  │   send_email_reply    │         │
│  │                       │  │                       │  │                       │         │
│  │  • Query Gmail API    │  │  • Fetch full email   │  │  • Validate draft     │         │
│  │  • Filter by query    │  │  • Parse content      │  │  • Create reply       │         │
│  │  • Return summary     │  │  • Generate AI draft  │  │  • Send via Gmail API │         │
│  │  • Cache in session   │  │  • Cache in session   │  │  • Return confirmation│         │
│  └───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘         │
│              │                          │                          │                     │
│              └──────────────────────────┼──────────────────────────┘                     │
│                                         │                                                │
│                                         ▼                                                │
│                           ┌───────────────────────────┐                                  │
│                           │    MAILBOX SESSION        │                                  │
│                           │                           │                                  │
│                           │  • Caches listed emails   │                                  │
│                           │  • Stores read emails     │                                  │
│                           │  • Manages draft replies  │                                  │
│                           │  • Thread context         │                                  │
│                           └───────────────────────────┘                                  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                           ╔═══════════════════════════╗
                           ║      GMAIL API            ║
                           ║   (Google Cloud)          ║
                           ║                           ║
                           ║  • messages.list          ║
                           ║  • messages.get           ║
                           ║  • messages.send          ║
                           ╚═══════════════════════════╝


═══════════════════════════════════════════════════════════════════════════════════════════

EMAIL PROCESSING WORKFLOW:

    ┌─────────────────┐
    │ 1. User Request │  "Show me my unread emails"
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 2. Agent Parse  │  LLM determines intent and required tool
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 3. Tool Call    │  list_emails(query="is:unread", max_results=10)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 4. Gmail API    │  Fetch emails from Gmail
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 5. Response     │  Format and present to user
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 6. User: "Read  │  "Read email #3"
    │    email #3"    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 7. Fetch Email  │  Get full email content
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ 8. Generate Draft Reply             │
    │                                     │
    │  ╔═════════════════════════════╗    │
    │  ║  LLM analyzes email content ║    │
    │  ║  and generates contextual   ║    │
    │  ║  draft reply                ║    │
    │  ╚═════════════════════════════╝    │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ 9. User Review  │  User can edit or approve draft
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ 10. Send Reply  │  Send via Gmail API (with user confirmation)
    └─────────────────┘


═══════════════════════════════════════════════════════════════════════════════════════════

LEGEND:
───── Sequential Flow          ═════ Component Boundary
╔═══╗ External Service         ┌────┐ Processing Unit
──►── Data Flow Direction      │    │ Agent/Component
"""


def generate_mermaid_diagram():
    """Generate Mermaid diagram of the workflow."""
    return """
graph TB
    User([User]) -->|Natural Language| App[FastAPI Application]
    
    subgraph Authentication["Authentication Flow"]
        App --> AuthURL[GET /auth/url]
        AuthURL --> Google[Google OAuth]
        Google --> Callback[POST /auth/callback]
        Callback --> Token[token.json]
    end
    
    subgraph AgentFlow["Agent Chat Flow"]
        App --> Chat[POST /agent/chat]
        Chat --> Agent[Gmail Agent]
        
        Agent --> SystemPrompt[System Prompt]
        SystemPrompt --> History[+ Conversation History]
        History --> UserMsg[+ User Message]
        UserMsg --> LLM
    end
    
    subgraph AILayer["AI Processing Layer"]
        LLM[Ollama LLM<br/>llama3.2 / qwen2.5]
        LLM --> Decision{Tool Call?}
        
        Decision -->|Yes| ToolChoice[Select Tool]
        Decision -->|No| DirectResponse[Direct Response]
        
        ToolChoice --> ListTool[list_emails]
        ToolChoice --> ReadTool[read_email]
        ToolChoice --> SendTool[send_email_reply]
    end
    
    subgraph ToolExecution["Tool Execution Layer"]
        ListTool --> Mailbox[Mailbox Session]
        ReadTool --> Mailbox
        SendTool --> Mailbox
        
        Mailbox --> GmailAPI[Gmail API]
        
        ReadTool --> DraftGen[AI Draft Generation]
        DraftGen --> LLM
    end
    
    GmailAPI --> Gmail[(Gmail<br/>Google Cloud)]
    
    Mailbox --> Response[Format Response]
    DirectResponse --> Response
    Response --> User
    
    style User fill:#e1f5e1
    style LLM fill:#ffe1e1
    style Gmail fill:#4285f4,color:#fff
    style Agent fill:#e1e1ff
    style Mailbox fill:#fff3cd
    style DraftGen fill:#f8d7da
    style Token fill:#d4edda
"""


def generate_html_diagram():
    """Generate an HTML file with both diagrams."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ayaan's Gmail Autoresponder Agent - Workflow Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .diagram-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .ascii-diagram {{
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.3;
        }}
        .component-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .component-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4285f4;
        }}
        .component-card.auth {{
            border-left-color: #34a853;
        }}
        .component-card.agent {{
            border-left-color: #ea4335;
        }}
        .component-card.tools {{
            border-left-color: #fbbc04;
        }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }}
        .tag.api {{
            background: #e8f0fe;
            color: #1967d2;
        }}
        .tag.ai {{
            background: #fce8e6;
            color: #c5221f;
        }}
        .tag.external {{
            background: #e6f4ea;
            color: #137333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background: #f8f9fa;
        }}
        code {{
            background: #f1f1f1;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <h1>📧 Ayaan's Gmail Autoresponder Agent - Workflow Diagram</h1>
    
    <div class="diagram-container">
        <h2>Interactive Mermaid Diagram</h2>
        <div class="mermaid">
{generate_mermaid_diagram()}
        </div>
    </div>
    
    <div class="diagram-container">
        <h2>ASCII Flow Diagram</h2>
        <pre class="ascii-diagram">{generate_ascii_diagram()}</pre>
    </div>
    
    <div class="diagram-container">
        <h2>System Components</h2>
        <div class="component-grid">
            <div class="component-card auth">
                <h3>🔐 Authentication</h3>
                <span class="tag api">REST API</span>
                <span class="tag external">Google OAuth</span>
                <ul>
                    <li><code>GET /auth/url</code> - Generate OAuth URL</li>
                    <li><code>POST /auth/callback</code> - Exchange code for token</li>
                    <li><code>GET /auth/status</code> - Check token status</li>
                    <li><code>POST /auth/refresh</code> - Refresh token</li>
                    <li><code>DELETE /auth/token</code> - Revoke access</li>
                </ul>
            </div>
            
            <div class="component-card agent">
                <h3>🤖 Gmail Agent</h3>
                <span class="tag ai">LLM-Powered</span>
                <span class="tag api">Tool Calling</span>
                <ul>
                    <li><b>Model:</b> Ollama (llama3.2 / qwen2.5)</li>
                    <li><b>Features:</b>
                        <ul>
                            <li>Natural language understanding</li>
                            <li>Tool selection and execution</li>
                            <li>Context-aware draft replies</li>
                            <li>Conversation history</li>
                        </ul>
                    </li>
                </ul>
            </div>
            
            <div class="component-card tools">
                <h3>🛠️ Agent Tools</h3>
                <span class="tag api">Functions</span>
                <table>
                    <tr>
                        <th>Tool</th>
                        <th>Purpose</th>
                    </tr>
                    <tr>
                        <td><code>list_emails</code></td>
                        <td>Query and list emails from inbox</td>
                    </tr>
                    <tr>
                        <td><code>read_email</code></td>
                        <td>Read email content + generate draft</td>
                    </tr>
                    <tr>
                        <td><code>send_email_reply</code></td>
                        <td>Send approved reply</td>
                    </tr>
                </table>
            </div>
            
            <div class="component-card">
                <h3>📬 Mailbox Session</h3>
                <span class="tag api">State Management</span>
                <ul>
                    <li><b>Email Cache:</b> Stores listed emails</li>
                    <li><b>Read Cache:</b> Stores full email content</li>
                    <li><b>Draft Storage:</b> AI-generated replies</li>
                    <li><b>Thread Context:</b> Reply threading info</li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="diagram-container">
        <h2>API Endpoints</h2>
        <table>
            <thead>
                <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>/health</code></td>
                    <td>GET</td>
                    <td>Health check and service status</td>
                </tr>
                <tr>
                    <td><code>/auth/url</code></td>
                    <td>GET</td>
                    <td>Get OAuth authorization URL</td>
                </tr>
                <tr>
                    <td><code>/auth/callback</code></td>
                    <td>POST</td>
                    <td>Submit authorization code</td>
                </tr>
                <tr>
                    <td><code>/auth/status</code></td>
                    <td>GET</td>
                    <td>Check token validity</td>
                </tr>
                <tr>
                    <td><code>/auth/refresh</code></td>
                    <td>POST</td>
                    <td>Refresh OAuth token</td>
                </tr>
                <tr>
                    <td><code>/auth/token</code></td>
                    <td>DELETE</td>
                    <td>Delete/revoke token</td>
                </tr>
                <tr>
                    <td><code>/emails/list</code></td>
                    <td>POST</td>
                    <td>List emails with query filter</td>
                </tr>
                <tr>
                    <td><code>/emails/read</code></td>
                    <td>POST</td>
                    <td>Read email and generate draft</td>
                </tr>
                <tr>
                    <td><code>/emails/reply</code></td>
                    <td>POST</td>
                    <td>Send email reply</td>
                </tr>
                <tr>
                    <td><code>/agent/chat</code></td>
                    <td>POST</td>
                    <td>Chat with AI agent</td>
                </tr>
                <tr>
                    <td><code>/agent/reset</code></td>
                    <td>POST</td>
                    <td>Reset conversation</td>
                </tr>
                <tr>
                    <td><code>/metrics</code></td>
                    <td>GET</td>
                    <td>Prometheus metrics</td>
                </tr>
                <tr>
                    <td><code>/workflow-diagram</code></td>
                    <td>GET</td>
                    <td>Interactive workflow diagram</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="diagram-container">
        <h2>Data Flow Summary</h2>
        <ol>
            <li><b>Authentication:</b> User authenticates via Google OAuth → Token stored locally</li>
            <li><b>User Request:</b> Natural language input to agent chat endpoint</li>
            <li><b>LLM Processing:</b> Ollama model interprets intent and selects appropriate tool</li>
            <li><b>Tool Execution:</b> Selected tool queries Gmail API via authenticated service</li>
            <li><b>Draft Generation:</b> For read operations, LLM generates contextual reply draft</li>
            <li><b>Response:</b> Formatted response returned to user</li>
            <li><b>Reply Send:</b> User-approved draft sent via Gmail API</li>
        </ol>
    </div>
</body>
</html>"""
    return html_content


# Save the diagrams if run directly
if __name__ == "__main__":
    # Save ASCII diagram
    with open("workflow_diagram.txt", "w", encoding="utf-8") as f:
        f.write(generate_ascii_diagram())
    
    # Save Mermaid diagram
    with open("workflow_diagram.mmd", "w", encoding="utf-8") as f:
        f.write(generate_mermaid_diagram())
    
    # Save HTML with both diagrams
    with open("workflow_diagram.html", "w", encoding="utf-8") as f:
        f.write(generate_html_diagram())
    
    print("Workflow diagrams generated:")
    print("  - workflow_diagram.txt (ASCII)")
    print("  - workflow_diagram.mmd (Mermaid)")
    print("  - workflow_diagram.html (Interactive HTML)")
