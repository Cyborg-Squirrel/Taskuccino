"""Taskuccino Discord bot library."""
from taskuccino._types import OllamaError, OllamaRequest, OllamaResponse
from taskuccino.ai_response_cog import AiResponseCog
from taskuccino.config import (BotConfig, Model, ModelsConfig, load_config,
                               load_system_prompt)
from taskuccino.ollama_client import OllamaClient

__version__ = "0.1.0"
__all__ = [
    "BotConfig",
    "Model",
    "ModelsConfig",
    "load_config",
    "load_system_prompt",
    "OllamaClient",
    "AiResponseCog",
    "OllamaRequest",
    "OllamaResponse",
    "OllamaError",
]
