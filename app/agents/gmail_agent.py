"""
Gmail Agent - AI-powered email assistant with tool calling.
"""
from typing import Optional, Callable
from googleapiclient.discovery import Resource

from app.clients.ollama_client import OllamaClientWrapper
from app.utils.mailbox_session import MailboxSession
from app.core.config import OLLAMA_MODEL


SYSTEM_PROMPT = """You are a helpful Gmail assistant. You can help users manage their emails.

Available tools:
1. list_emails - List emails from the inbox. Use query parameter for filtering (e.g., "is:unread", "from:someone@email.com")
2. read_email - Read the full content of an email by its number. This also generates a draft reply.
3. send_email_reply - Send a reply to an email. ONLY use this after the user explicitly approves the draft.

IMPORTANT RULES:
- When user asks to see their emails, use list_emails
- When user wants to read an email, use read_email with the email number
- NEVER send an email without explicit user approval
- Always show the draft to the user and ask for confirmation before sending
- Be helpful and concise in your responses
"""

# Tool definitions for Ollama function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "List emails from Gmail inbox. Returns numbered list of emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Gmail search query like 'is:unread', 'from:someone@email.com', 'subject:meeting'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": "Read the full content of an email by its number and generate a draft reply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_number": {
                        "type": "integer",
                        "description": "The number of the email to read (from list_emails)"
                    }
                },
                "required": ["email_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_reply",
            "description": "Send a reply to an email. Only use after user approves the draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_number": {
                        "type": "integer",
                        "description": "The number of the email to reply to"
                    },
                    "reply_body": {
                        "type": "string",
                        "description": "Custom reply text (optional, uses generated draft if not provided)"
                    }
                },
                "required": ["email_number"]
            }
        }
    }
]


class GmailAgent:
    """
    AI-powered Gmail agent that can list, read, and send emails
    using natural language conversation.
    """

    def __init__(
        self,
        ollama_client: OllamaClientWrapper,
        gmail_service: Resource,
        mailbox: Optional[MailboxSession] = None
    ):
        self.client = ollama_client
        self.gmail_service = gmail_service
        self.mailbox = mailbox or MailboxSession()
        self.conversation_history: list[dict] = []
        self.tools = AGENT_TOOLS
        
        # Tool function dispatch table
        self.tool_functions: dict[str, Callable] = {
            "list_emails": self._tool_list_emails,
            "read_email": self._tool_read_email,
            "send_email_reply": self._tool_send_reply,
        }

    def _tool_list_emails(self, max_results: int = 10, query: str = "is:unread") -> dict:
        """Tool wrapper for list_emails."""
        return self.mailbox.list_emails(self.gmail_service, max_results, query)

    def _tool_read_email(self, email_number: int) -> dict:
        """Tool wrapper for read_email."""
        return self.mailbox.read_email(self.gmail_service, email_number)

    def _tool_send_reply(self, email_number: int, reply_body: Optional[str] = None) -> dict:
        """Tool wrapper for send_email_reply."""
        return self.mailbox.send_reply(self.gmail_service, email_number, reply_body)

    def reset(self) -> None:
        """Reset conversation history and mailbox session."""
        self.conversation_history.clear()
        self.mailbox.clear()

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            The agent's response text
        """
        import json
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build full message list with system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + self.conversation_history

        # Call Ollama with tools
        response = self.client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=self.tools,
            stream=False
        )

        assistant_message = response.get("message", {})

        # Check for tool calls
        tool_calls = assistant_message.get("tool_calls", [])
        
        if tool_calls:
            # Add assistant's tool call message to history
            self.conversation_history.append(assistant_message)

            # Execute each tool call
            for tool_call in tool_calls:
                func_name = tool_call.get("function", {}).get("name", "")
                func_args = tool_call.get("function", {}).get("arguments", {})
                
                # Handle string arguments (some models return JSON string)
                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except json.JSONDecodeError:
                        func_args = {}

                # Execute the function
                if func_name in self.tool_functions:
                    result = self.tool_functions[func_name](**func_args)
                else:
                    result = {"error": f"Unknown function: {func_name}"}

                # Add tool result to history
                self.conversation_history.append({
                    "role": "tool",
                    "content": json.dumps(result, default=str)
                })

            # Get final response after tool execution
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + self.conversation_history

            final_response = self.client.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                tools=self.tools,
                stream=False
            )

            final_content = final_response.get("message", {}).get("content", "")
            self.conversation_history.append({
                "role": "assistant",
                "content": final_content
            })
            return final_content

        else:
            # No tool call, just return text response
            content = assistant_message.get("content", "")
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })
            return content
