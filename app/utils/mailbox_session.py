"""
Mailbox Session - Maintains state for email listing and operations.
"""
from typing import Optional, Literal
from googleapiclient.discovery import Resource

from app.utils.email_utils import (
    extract_email_body,
    parse_email_address,
    create_reply_message,
)
from app.clients.ollama_client import get_ollama_client
from app.core.config import OLLAMA_MODEL


# Reply tone types - Normal, Friendly, Professional
ReplyTone = Literal["normal", "friendly", "professional"]


class MailboxSession:
    """
    Maintains mapping between displayed numbers (1-N)
    and Gmail message IDs. Also stores last generated draft.
    
    This allows users to reference emails by simple numbers
    rather than complex Gmail IDs.
    """

    def __init__(self):
        self.index_map: dict[int, str] = {}  # {number: gmail_message_id}
        self.last_draft: Optional[str] = None
        self.last_number: Optional[int] = None
        self.email_cache: dict[int, dict] = {}  # Cache read emails for regeneration

    def clear(self) -> None:
        """Clear the session state."""
        self.index_map.clear()
        self.last_draft = None
        self.last_number = None
        self.email_cache.clear()

    def list_emails(
        self,
        service: Resource,
        max_results: int = 10,
        query: str = "is:unread"
    ) -> dict:
        """
        List emails from Gmail inbox.
        
        Args:
            service: Gmail API service
            max_results: Maximum number of emails to return
            query: Gmail search query
            
        Returns:
            Dict with 'emails' list or 'error'
        """
        try:
            results = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            self.index_map.clear()

            if not messages:
                return {"emails": [], "message": "No emails found matching the query."}

            emails = []
            for i, msg in enumerate(messages, start=1):
                data = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()

                headers = {
                    h["name"]: h["value"]
                    for h in data.get("payload", {}).get("headers", [])
                }
                
                self.index_map[i] = msg["id"]

                emails.append({
                    "number": i,
                    "id": msg["id"],
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(No Subject)"),
                    "date": headers.get("Date", ""),
                    "snippet": data.get("snippet", "")[:120]
                })

            return {"emails": emails, "count": len(emails)}

        except Exception as e:
            return {"error": str(e)}

    def read_email(
        self,
        service: Resource,
        number: int,
        generate_draft: bool = True,
        tone: ReplyTone = "normal"
    ) -> dict:
        """
        Read full content of an email and optionally generate a draft reply.
        
        Args:
            service: Gmail API service
            number: Email number from list
            generate_draft: Whether to generate an AI draft reply
            tone: Reply tone - "normal", "friendly", or "professional"
            
        Returns:
            Dict with email content and draft, or 'error'
        """
        email_id = self.index_map.get(number)
        if not email_id:
            return {"error": f"Invalid email number {number}. Please list emails first."}

        try:
            msg = service.users().messages().get(
                userId="me",
                id=email_id,
                format="full"
            ).execute()

            headers = {
                h["name"]: h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            body = extract_email_body(msg.get("payload", {}))
            
            result = {
                "number": number,
                "id": email_id,
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(No Subject)"),
                "date": headers.get("Date", ""),
                "body": body,
                "thread_id": msg.get("threadId"),
            }
            
            # Cache the email for regeneration
            self.email_cache[number] = {
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "body": body
            }

            # Generate draft reply using LLM
            if generate_draft:
                draft = self._generate_draft(
                    from_addr=headers.get("From", ""),
                    subject=headers.get("Subject", ""),
                    body=body,
                    tone=tone
                )
                result["draft_reply"] = draft
                result["tone"] = tone
                self.last_draft = draft
                self.last_number = number

            return result

        except Exception as e:
            return {"error": str(e)}

    def regenerate_draft(
        self,
        number: int,
        tone: ReplyTone = "normal"
    ) -> dict:
        """
        Regenerate a draft reply for a cached email with a specific tone.
        
        Args:
            number: Email number
            tone: Reply tone - "normal", "friendly", or "professional"
            
        Returns:
            Dict with new draft or 'error'
        """
        if number not in self.email_cache:
            return {"error": f"Email {number} not found in cache. Please read the email first."}
        
        cached = self.email_cache[number]
        
        try:
            draft = self._generate_draft(
                from_addr=cached["from"],
                subject=cached["subject"],
                body=cached["body"],
                tone=tone
            )
            
            self.last_draft = draft
            self.last_number = number
            
            return {
                "number": number,
                "draft_reply": draft,
                "tone": tone
            }
        except Exception as e:
            return {"error": str(e)}

    def _generate_draft(
        self, 
        from_addr: str, 
        subject: str, 
        body: str,
        tone: ReplyTone = "normal"
    ) -> str:
        """Generate a draft reply using the LLM with specified tone."""
        import re
        
        print(f"\n{'='*60}")
        print(f"🎯 GENERATING DRAFT WITH TONE: {tone.upper()}")
        print(f"{'='*60}")
        
        # Define tone-specific configurations with exact signatures
        tone_configs = {
            "normal": {
                "instruction": (
                    "Write a NORMAL, straightforward email reply. "
                    "Use a balanced tone that is neither too formal nor too casual. "
                    "Be clear, helpful, and polite. "
                    "Keep it simple and to the point."
                ),
                "signature": "Regards,\nAyaan",
                "temperature": 0.7
            },
            "friendly": {
                "instruction": (
                    "Write a WARM, FRIENDLY, and CASUAL reply. "
                    "Use a conversational, approachable tone like you're writing to a friend. "
                    "Feel free to use casual expressions, contractions, and show enthusiasm! "
                    "Add warmth with phrases like 'Hey!', 'Thanks so much!', 'That sounds great!'. "
                    "Use exclamation points where appropriate to convey energy and positivity. "
                    "Be personable, genuine, and make the recipient feel valued."
                ),
                "signature": "Regards,\nAyaan",
                "temperature": 0.9
            },
            "professional": {
                "instruction": (
                    "Write a FORMAL and PROFESSIONAL reply suitable for official correspondence. "
                    "Use formal language with proper salutations like 'Dear Sir/Madam' or 'Dear Mr./Ms. [Name]'. "
                    "Maintain a serious, respectful, and professional tone throughout. "
                    "Use formal phrases like 'I am writing to...', 'Thank you for your correspondence...'. "
                    "Avoid contractions (use 'I am' not 'I'm', 'do not' not 'don't'). "
                    "Be precise, structured, and courteous."
                ),
                "signature": "Regards,\nAyaan Asish\nGrade 11\nWest Carleton Secondary School, Ontario",
                "temperature": 0.5
            }
        }
        
        config = tone_configs.get(tone, tone_configs["normal"])
        instruction = config["instruction"]
        signature = config["signature"]
        temperature = config["temperature"]
        
        print(f"📝 Using temperature: {temperature}")
        print(f"📝 Signature: {signature.replace(chr(10), ' | ')}")
        
        try:
            client = get_ollama_client()
            
            prompt = (
                f"You are an email assistant writing on behalf of Ayaan. Write a reply in a SPECIFIC tone.\n\n"
                f"=== TONE: {tone.upper()} ===\n"
                f"{instruction}\n\n"
                f"=== ORIGINAL EMAIL ===\n"
                f"From: {from_addr}\n"
                f"Subject: {subject}\n\n"
                f"{body}\n"
                f"=== END OF EMAIL ===\n\n"
                f"=== CRITICAL INSTRUCTIONS ===\n"
                f"1. Write ONLY the email body content\n"
                f"2. Do NOT include any Subject line or email headers\n"
                f"3. Do NOT add ANY signature or closing at the end\n"
                f"4. Do NOT write 'Regards', 'Best regards', 'Sincerely', 'Thanks', 'Cheers', or ANY closing phrase\n"
                f"5. Do NOT sign off with any name\n"
                f"6. Just write the main message content and STOP\n"
                f"7. The tone MUST be clearly {tone.upper()}\n\n"
                f"Write the reply body now (NO signature, NO closing):"
            )
            
            print(f"\n📤 Sending prompt to LLM...")
            draft = client.generate_text(prompt, OLLAMA_MODEL, temperature=temperature)
            
            print(f"\n📥 Received draft (first 200 chars): {draft[:200] if draft else 'EMPTY'}...")
            
            if not draft or not draft.strip():
                draft = f"Thank you for your email regarding '{subject}'. I will review and respond shortly."
            
            # Clean up the draft
            draft = draft.strip()
            
            # Remove common signature patterns that LLM might have added
            # Pattern to match various closings at the end of the text
            closing_patterns = [
                r'\n\s*(Best regards|Kind regards|Regards|Sincerely|Thanks|Thank you|Cheers|Warm regards|Best|Yours truly|Yours sincerely|Warmly|Take care|With appreciation)[,.]?\s*\n?\s*(Ayaan.*)?$',
                r'\n\s*(Best regards|Kind regards|Regards|Sincerely|Thanks|Thank you|Cheers|Warm regards|Best|Yours truly|Yours sincerely|Warmly|Take care|With appreciation)[,.]?\s*$',
                r'\n\s*-?\s*Ayaan.*$',
            ]
            
            for pattern in closing_patterns:
                draft = re.sub(pattern, '', draft, flags=re.IGNORECASE | re.DOTALL).strip()
            
            # Add the correct signature
            final_draft = f"{draft}\n\n{signature}"
            
            print(f"✅ Final draft with signature added")
            print(f"{'='*60}\n")
            
            return final_draft
            
        except Exception as e:
            print(f"❌ Error generating draft: {e}")
            # Fallback draft on LLM failure with appropriate signature
            return f"Thank you for your email regarding '{subject}'. I will review and respond shortly.\n\n{signature}"

    def send_reply(
        self,
        service: Resource,
        number: int,
        reply_body: Optional[str] = None
    ) -> dict:
        """
        Send a reply to an email.
        
        Args:
            service: Gmail API service
            number: Email number to reply to
            reply_body: Custom reply body (uses last draft if None)
            
        Returns:
            Dict with success status or 'error'
        """
        email_id = self.index_map.get(number)
        if not email_id:
            return {"error": f"Invalid email number {number}. Please list emails first."}

        # Use last draft if no body provided
        if reply_body is None:
            if self.last_number != number or not self.last_draft:
                return {"error": "No draft available for this email. Please read the email first to generate a draft."}
            reply_body = self.last_draft

        try:
            # Get original message for headers
            orig = service.users().messages().get(
                userId="me",
                id=email_id,
                format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()

            headers = {
                h["name"]: h["value"]
                for h in orig.get("payload", {}).get("headers", [])
            }

            to_addr = parse_email_address(headers.get("From", ""))
            subject = headers.get("Subject", "")
            thread_id = orig.get("threadId")

            # Create and send message
            message = create_reply_message(to_addr, subject, reply_body, thread_id)
            
            service.users().messages().send(
                userId="me",
                body=message
            ).execute()

            # Clear draft after successful send
            if self.last_number == number:
                self.last_draft = None
                self.last_number = None

            return {
                "success": True,
                "sent_to": to_addr,
                "subject": subject if subject.lower().startswith("re:") else f"Re: {subject}"
            }

        except Exception as e:
            return {"error": str(e)}
