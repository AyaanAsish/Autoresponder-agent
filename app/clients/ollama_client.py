"""
Ollama Cloud Client wrapper with proper error handling.
Supports both local Ollama and Ollama Cloud API.
"""
from typing import Optional
import httpx
from app.core.config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaClientWrapper:
    """
    Wrapper for Ollama API with better error handling.
    Uses httpx for direct API calls to support cloud endpoints.
    """

    def __init__(self, host: str, api_key: str):
        self.host = host.rstrip('/')
        self.api_key = api_key
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._http_client = httpx.Client(
                headers=headers,
                timeout=120.0,  # 2 minutes for slow models
                verify=False  # Skip SSL verification for some cloud endpoints
            )
        return self._http_client

    def chat(
        self,
        model: str,
        messages: list[dict],
        tools: Optional[list] = None,
        options: Optional[dict] = None,
        stream: bool = False
    ) -> dict:
        """
        Send a chat request to Ollama API.
        
        Args:
            model: The model to use
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            options: Optional dict of model options (temperature, top_p, etc.)
            stream: Whether to stream the response
        
        Returns:
            dict with 'message' containing 'content' and optionally 'tool_calls'
        """
        url = f"{self.host}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
        if options:
            payload["options"] = options

        print(f"🌐 Calling Ollama API: {url}")
        print(f"📦 Model: {model}, Stream: {stream}, Options: {options}")
        
        try:
            response = self.http_client.post(url, json=payload)
            
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text[:500]
                print(f"❌ API Error: {error_text}")
                raise Exception(f"Ollama API error {response.status_code}: {error_text}")
            
            # Handle streaming response (multiple JSON lines)
            # Ollama returns newline-delimited JSON when streaming
            response_text = response.text
            
            if '\n' in response_text:
                # Streaming response - concatenate all content
                import json
                full_content = ""
                last_response = None
                
                for line in response_text.strip().split('\n'):
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                full_content += chunk['message']['content']
                            last_response = chunk
                        except json.JSONDecodeError:
                            continue
                
                # Return in standard format
                return {
                    "message": {
                        "role": "assistant",
                        "content": full_content
                    },
                    "done": True
                }
            else:
                # Non-streaming response
                data = response.json()
                return data
            
        except httpx.ConnectError as e:
            print(f"❌ Connection error: {e}")
            raise Exception(f"Failed to connect to Ollama at {self.host}: {e}")
        except httpx.TimeoutException as e:
            print(f"❌ Timeout error: {e}")
            raise Exception(f"Ollama request timed out: {e}")
        except Exception as e:
            print(f"❌ Request error: {e}")
            raise

    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Simple text generation helper.
        
        Args:
            prompt: The prompt to send
            model: Model to use (defaults to OLLAMA_MODEL)
            temperature: Controls randomness (0.0-1.0, higher = more creative)
        
        Returns:
            The generated text content.
        """
        model = model or OLLAMA_MODEL
        response = self.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature},
            stream=True  # Enable streaming for cloud API
        )
        
        # Ollama returns: {'message': {'role': 'assistant', 'content': '...'}}
        message = response.get("message", {})
        content = message.get("content", "")
        
        # Some models wrap response in thinking tags, extract the actual response
        if "<think>" in content and "</think>" in content:
            # Remove thinking section
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        print(f"✅ Generated content length: {len(content)} chars")
        return content

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to Ollama.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = self.generate_text("Say 'Hello' in one word.", OLLAMA_MODEL, temperature=0.1)
            return True, response[:100] if response else "Connected but empty response"
        except Exception as e:
            return False, str(e)


# Singleton instance
_ollama_client: Optional[OllamaClientWrapper] = None


def get_ollama_client() -> OllamaClientWrapper:
    """Get or create the Ollama client singleton."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClientWrapper(
            host=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY
        )
    return _ollama_client
