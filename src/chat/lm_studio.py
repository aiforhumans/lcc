"""
LM Studio client for Local Chat Companion.

Provides HTTP API communication with LM Studio's REST API (beta) and OpenAI-compatible endpoints.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum

import httpx

# Optional import with fallback
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    import logging
    structlog = logging
    STRUCTLOG_AVAILABLE = False

from ..core.config import Config
from ..core.logging_config import LoggerMixin


class LMStudioError(Exception):
    """Base exception for LM Studio related errors."""
    pass


class ModelNotLoadedError(LMStudioError):
    """Raised when trying to use a model that isn't loaded."""
    pass


class ConnectionError(LMStudioError):
    """Raised when unable to connect to LM Studio."""
    pass


@dataclass
class ModelInfo:
    """Information about a model from LM Studio."""
    id: str
    type: str
    publisher: str
    architecture: str
    quantization: str
    state: str  # "loaded" or "not-loaded"
    max_context_length: int
    format: str = ""
    
    @property
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self.state == "loaded"


@dataclass
class UsageStats:
    """Token usage statistics from LM Studio."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class PerformanceStats:
    """Performance statistics from LM Studio."""
    tokens_per_second: float
    time_to_first_token: float
    generation_time: float
    stop_reason: str


@dataclass
class RuntimeInfo:
    """Runtime information from LM Studio."""
    name: str
    version: str
    supported_formats: List[str]


@dataclass
class ChatMessage:
    """A chat message with role and content."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from LM Studio chat completion."""
    message: ChatMessage
    usage: UsageStats
    stats: PerformanceStats
    model_info: Dict[str, Any]
    runtime: RuntimeInfo
    id: str
    created: int
    finish_reason: str


class LMStudioClient(LoggerMixin):
    """Client for communicating with LM Studio's REST API."""
    
    def __init__(self, config: Config):
        """Initialize the LM Studio client."""
        self.config = config
        self.base_url = config.lm_studio_api_base.rstrip('/')
        self.api_key = config.lm_studio_api_key
        self.default_model = config.default_model
        
        # Use LM Studio's native REST API (beta) for richer metadata
        self.native_api_base = self.base_url.replace('/v1', '/api/v0')
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.client = None
        
        self.log_with_context(
            "info",
            "LM Studio client initialized",
            base_url=self.base_url,
            native_api_base=self.native_api_base,
            default_model=self.default_model
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        use_native_api: bool = True
    ) -> Dict[str, Any]:
        """Make an HTTP request to LM Studio."""
        if not self.client:
            raise LMStudioError("Client not initialized. Use as async context manager.")
        
        base_url = self.native_api_base if use_native_api else self.base_url
        url = f"{base_url}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            self.logger.debug(
                "Making request to LM Studio",
                method=method,
                url=url,
                data=data
            )
            
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            else:
                response = await self.client.post(
                    url, 
                    headers=headers, 
                    json=data
                )
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.debug(
                "Request successful",
                status_code=response.status_code,
                response_size=len(response.content)
            )
            
            return result
            
        except httpx.ConnectError as e:
            self.log_with_context("error", "Failed to connect to LM Studio", error=str(e))
            raise ConnectionError(f"Could not connect to LM Studio at {url}. Is LM Studio running?") from e
        
        except httpx.HTTPStatusError as e:
            self.log_with_context(
                "error",
                "HTTP error from LM Studio",
                status_code=e.response.status_code,
                response_text=e.response.text
            )
            raise LMStudioError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        
        except json.JSONDecodeError as e:
            self.log_with_context("error", "Invalid JSON response from LM Studio", error=str(e))
            raise LMStudioError("Invalid JSON response from LM Studio") from e
        
        except Exception as e:
            self.log_with_context("error", "Unexpected error in LM Studio request", error=str(e), exc_info=True)
            raise LMStudioError(f"Unexpected error: {e}") from e
    
    async def list_models(self) -> List[ModelInfo]:
        """List all available models in LM Studio."""
        try:
            response = await self._make_request("GET", "/models")
            models = []
            
            for model_data in response.get("data", []):
                model = ModelInfo(
                    id=model_data.get("id", ""),
                    type=model_data.get("type", ""),
                    publisher=model_data.get("publisher", ""),
                    architecture=model_data.get("arch", ""),
                    quantization=model_data.get("quant", ""),
                    state=model_data.get("state", "unknown"),
                    max_context_length=model_data.get("context_length", 0),
                    format=model_data.get("format", "")
                )
                models.append(model)
            
            self.logger.info(f"Retrieved {len(models)} models from LM Studio")
            return models
            
        except Exception as e:
            self.log_with_context("error", "Failed to list models", error=str(e))
            raise
    
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed information about a specific model."""
        try:
            response = await self._make_request("GET", f"/models/{model_id}")
            
            model = ModelInfo(
                id=response.get("id", model_id),
                type=response.get("type", ""),
                publisher=response.get("publisher", ""),
                architecture=response.get("arch", ""),
                quantization=response.get("quant", ""),
                state=response.get("state", "unknown"),
                max_context_length=response.get("context_length", 0),
                format=response.get("format", "")
            )
            
            self.log_with_context("debug", f"Retrieved info for model {model_id}", model_state=model.state)
            return model
            
        except Exception as e:
            self.log_with_context("error", f"Failed to get model info for {model_id}", error=str(e))
            raise
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> ChatResponse:
        """Generate a chat completion using LM Studio's native REST API."""
        model_id = model or self.default_model
        
        # Check if model is loaded
        try:
            model_info = await self.get_model_info(model_id)
            if not model_info.is_loaded:
                raise ModelNotLoadedError(f"Model '{model_id}' is not loaded in LM Studio")
        except LMStudioError:
            # If we can't get model info, try anyway (might be OpenAI compatibility mode)
            self.logger.warning(f"Could not verify if model {model_id} is loaded")
        
        request_data = {
            "model": model_id,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": stream
        }
        
        # Add optional parameters
        if temperature is not None:
            request_data["temperature"] = temperature
        else:
            request_data["temperature"] = self.config.temperature
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        else:
            request_data["max_tokens"] = self.config.max_tokens
        
        # Add other model parameters from config
        request_data.update({
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty
        })
        
        try:
            response = await self._make_request("POST", "/chat/completions", request_data)
            
            # Parse the response
            choice = response["choices"][0]
            message_data = choice["message"]
            
            # Parse stats and metadata
            usage = UsageStats(
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                total_tokens=response["usage"]["total_tokens"]
            )
            
            stats = PerformanceStats(
                tokens_per_second=response["stats"]["tokens_per_second"],
                time_to_first_token=response["stats"]["time_to_first_token"],
                generation_time=response["stats"]["generation_time"],
                stop_reason=response["stats"].get("stop_reason", choice.get("finish_reason", "unknown"))
            )
            
            runtime = RuntimeInfo(
                name=response["runtime"]["name"],
                version=response["runtime"]["version"],
                supported_formats=response["runtime"]["supported_formats"]
            )
            
            chat_response = ChatResponse(
                message=ChatMessage(role=message_data["role"], content=message_data["content"]),
                usage=usage,
                stats=stats,
                model_info=response["model_info"],
                runtime=runtime,
                id=response["id"],
                created=response["created"],
                finish_reason=choice.get("finish_reason", "unknown")
            )
            
            self.logger.info(
                "Chat completion successful",
                model=model_id,
                tokens_generated=usage.completion_tokens,
                tokens_per_second=stats.tokens_per_second,
                finish_reason=chat_response.finish_reason
            )
            
            return chat_response
            
        except Exception as e:
            self.logger.error(
                "Chat completion failed",
                model=model_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if LM Studio is accessible and responsive."""
        try:
            # Try to list models as a health check
            models = await self.list_models()
            loaded_models = [m for m in models if m.is_loaded]
            
            health_info = {
                "status": "healthy",
                "total_models": len(models),
                "loaded_models": len(loaded_models),
                "available_models": [m.id for m in loaded_models]
            }
            
            self.log_with_context("info", "LM Studio health check passed", **health_info)
            return health_info
            
        except Exception as e:
            health_info = {
                "status": "unhealthy",
                "error": str(e)
            }
            self.log_with_context("error", "LM Studio health check failed", **health_info)
            return health_info
    
    async def ensure_model_loaded(self, model_id: Optional[str] = None) -> bool:
        """Ensure a model is loaded and ready for use."""
        model_id = model_id or self.default_model
        
        try:
            model_info = await self.get_model_info(model_id)
            if model_info.is_loaded:
                self.logger.info(f"Model {model_id} is already loaded")
                return True
            else:
                self.logger.warning(f"Model {model_id} is not loaded")
                return False
                
        except Exception as e:
            self.log_with_context("error", f"Could not check model status for {model_id}", error=str(e))
            return False
