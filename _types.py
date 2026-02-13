"""
Type definitions.
"""

from dataclasses import dataclass


@dataclass
class OllamaRequest:
    """Represents a request to process with Ollama."""

    channel_id: int
    message_id: int
    content: str
    image_attachments: list[bytes]

    def __init__(
        self,
        channel_id: int,
        message_id: int,
        content: str,
        image_attachments: list[bytes],
    ):
        self.channel_id = channel_id
        self.message_id = message_id
        self.content = content
        self.image_attachments = image_attachments


@dataclass
class OllamaResponse:
    """Represents a response from Ollama."""

    content: str
    request: OllamaRequest

    def __init__(self, content: str, request: OllamaRequest):
        self.content = content
        self.request = request


@dataclass
class OllamaError:
    """Represents an error communicating with Ollama."""

    error: object
    request: OllamaRequest

    def __init__(self, error: object, request: OllamaRequest):
        self.error = error
        self.request = request
