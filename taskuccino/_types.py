"""
Type definitions.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChatRole(Enum):
    """Role of a message in a chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """Represents a chat message from the user or the bot."""

    role: ChatRole
    content: str
    timestamp: datetime

@dataclass
class DiscordMessage(ChatMessage):
    """Represents a Discord chat message"""

    channel_id: int
    message_id: int
    image_attachments: list[bytes]

@dataclass
class OllamaRequest:
    """Represents a request to process with Ollama."""

    message: ChatMessage
    history: list[ChatMessage]


@dataclass
class OllamaResponse:
    """Represents a response from Ollama."""

    content: str
    request: OllamaRequest


@dataclass
class OllamaError(OllamaResponse):
    """Represents an error communicating with Ollama."""

    error: object
