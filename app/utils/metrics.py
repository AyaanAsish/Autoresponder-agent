"""
Metrics collection for Gmail Autoresponder Agent using Prometheus.

Provides comprehensive metrics for agent operations and system-wide performance tracking.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import asyncio
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# =============================================================================
# System-wide Metrics
# =============================================================================

# Info metrics for system information
system_info = Info(
    'gmail_agent_info',
    'Gmail Autoresponder Agent system information',
    registry=REGISTRY
)

# Overall request metrics
api_requests_total = Counter(
    'gmail_agent_api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status_code'],
    registry=REGISTRY
)

api_request_duration = Histogram(
    'gmail_agent_api_request_duration_seconds',
    'Duration of API request processing',
    ['endpoint', 'method'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2.5, 5, 10),
    registry=REGISTRY
)

# =============================================================================
# Gmail Operations Metrics
# =============================================================================

gmail_operations_total = Counter(
    'gmail_agent_gmail_operations_total',
    'Total number of Gmail operations',
    ['operation', 'status'],  # operation: list_emails, read_email, send_reply
    registry=REGISTRY
)

gmail_operation_duration = Histogram(
    'gmail_agent_gmail_operation_duration_seconds',
    'Duration of Gmail operations',
    ['operation'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
    registry=REGISTRY
)

emails_listed = Summary(
    'gmail_agent_emails_listed',
    'Number of emails returned in list operations',
    registry=REGISTRY
)

emails_read = Counter(
    'gmail_agent_emails_read_total',
    'Total number of emails read',
    registry=REGISTRY
)

emails_sent = Counter(
    'gmail_agent_emails_sent_total',
    'Total number of emails/replies sent',
    registry=REGISTRY
)

# =============================================================================
# Authentication Metrics
# =============================================================================

auth_operations_total = Counter(
    'gmail_agent_auth_operations_total',
    'Total number of authentication operations',
    ['operation', 'status'],  # operation: get_url, callback, refresh, delete
    registry=REGISTRY
)

token_status = Gauge(
    'gmail_agent_token_valid',
    'Whether the OAuth token is valid (1) or not (0)',
    registry=REGISTRY
)

# =============================================================================
# Agent/AI Metrics
# =============================================================================

agent_chat_total = Counter(
    'gmail_agent_chat_requests_total',
    'Total number of agent chat requests',
    ['status'],
    registry=REGISTRY
)

agent_chat_duration = Histogram(
    'gmail_agent_chat_duration_seconds',
    'Duration of agent chat processing',
    buckets=(0.5, 1, 2, 5, 10, 30, 60),
    registry=REGISTRY
)

agent_tool_calls_total = Counter(
    'gmail_agent_tool_calls_total',
    'Total number of tool calls made by the agent',
    ['tool_name', 'status'],
    registry=REGISTRY
)

agent_conversation_length = Summary(
    'gmail_agent_conversation_length',
    'Length of conversation history',
    registry=REGISTRY
)

draft_replies_generated = Counter(
    'gmail_agent_draft_replies_generated_total',
    'Total number of AI draft replies generated',
    registry=REGISTRY
)

# =============================================================================
# LLM/Ollama Metrics
# =============================================================================

ollama_requests_total = Counter(
    'gmail_agent_ollama_requests_total',
    'Total number of Ollama LLM requests',
    ['model', 'status'],
    registry=REGISTRY
)

ollama_request_duration = Histogram(
    'gmail_agent_ollama_request_duration_seconds',
    'Duration of Ollama LLM requests',
    ['model'],
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120),
    registry=REGISTRY
)

ollama_connection_status = Gauge(
    'gmail_agent_ollama_connected',
    'Whether Ollama is connected (1) or not (0)',
    registry=REGISTRY
)

# =============================================================================
# Error Metrics
# =============================================================================

errors_total = Counter(
    'gmail_agent_errors_total',
    'Total number of errors',
    ['component', 'error_type'],
    registry=REGISTRY
)

# =============================================================================
# Resource Metrics
# =============================================================================

memory_usage = Gauge(
    'gmail_agent_memory_usage_bytes',
    'Current memory usage in bytes',
    registry=REGISTRY
)

active_sessions = Gauge(
    'gmail_agent_active_sessions',
    'Number of active mailbox sessions',
    registry=REGISTRY
)


# =============================================================================
# Metric Collection Utilities
# =============================================================================

class MetricsCollector:
    """Singleton metrics collector for Gmail Autoresponder Agent."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.start_time = time.time()
        
        # Set system info
        system_info.info({
            'version': '1.0.0',
            'app_name': 'Gmail Autoresponder Agent',
            'environment': 'production'
        })
    
    @contextmanager
    def track_duration(self, histogram: Histogram, labels: Dict[str, str] = None):
        """Context manager to track duration of operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if labels:
                histogram.labels(**labels).observe(duration)
            else:
                histogram.observe(duration)
    
    def track_gmail_operation(self, operation: str):
        """Decorator to track Gmail operations."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, dict) and "error" in result:
                        status = "error"
                    return result
                except Exception as e:
                    status = "error"
                    errors_total.labels(component="gmail", error_type=type(e).__name__).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    gmail_operations_total.labels(operation=operation, status=status).inc()
                    gmail_operation_duration.labels(operation=operation).observe(duration)
            
            return wrapper
        return decorator
    
    def track_api_request(self, endpoint: str, method: str):
        """Decorator to track API request metrics."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status_code = 200
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = getattr(e, 'status_code', 500)
                    raise
                finally:
                    duration = time.time() - start_time
                    api_requests_total.labels(
                        endpoint=endpoint, 
                        method=method, 
                        status_code=str(status_code)
                    ).inc()
                    api_request_duration.labels(
                        endpoint=endpoint, 
                        method=method
                    ).observe(duration)
            
            return wrapper
        return decorator
    
    def track_ollama_request(self, model: str):
        """Decorator to track Ollama LLM request metrics."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    errors_total.labels(component="ollama", error_type=type(e).__name__).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    ollama_requests_total.labels(model=model, status=status).inc()
                    ollama_request_duration.labels(model=model).observe(duration)
            
            return wrapper
        return decorator
    
    def record_email_listed(self, count: int):
        """Record number of emails listed."""
        emails_listed.observe(count)
    
    def record_email_read(self):
        """Record an email being read."""
        emails_read.inc()
    
    def record_email_sent(self):
        """Record an email being sent."""
        emails_sent.inc()
    
    def record_draft_generated(self):
        """Record a draft reply being generated."""
        draft_replies_generated.inc()
    
    def record_agent_chat(self, status: str, duration: float, conversation_length: int):
        """Record agent chat metrics."""
        agent_chat_total.labels(status=status).inc()
        agent_chat_duration.observe(duration)
        agent_conversation_length.observe(conversation_length)
    
    def record_tool_call(self, tool_name: str, status: str):
        """Record a tool call made by the agent."""
        agent_tool_calls_total.labels(tool_name=tool_name, status=status).inc()
    
    def record_auth_operation(self, operation: str, status: str):
        """Record an authentication operation."""
        auth_operations_total.labels(operation=operation, status=status).inc()
    
    def set_token_status(self, is_valid: bool):
        """Set the token validity status."""
        token_status.set(1 if is_valid else 0)
    
    def set_ollama_status(self, is_connected: bool):
        """Set the Ollama connection status."""
        ollama_connection_status.set(1 if is_connected else 0)
    
    def update_resource_metrics(self):
        """Update resource usage metrics."""
        try:
            import psutil
            
            # Memory usage
            process = psutil.Process()
            memory_usage.set(process.memory_info().rss)
        except ImportError:
            # psutil not installed
            pass
    
    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics output."""
        # Update resource metrics before generating output
        self.update_resource_metrics()
        
        # Generate metrics in Prometheus format
        return generate_latest(REGISTRY)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_output() -> bytes:
    """Get current metrics in Prometheus format."""
    return metrics_collector.get_metrics()
