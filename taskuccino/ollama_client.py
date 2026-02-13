"""Ollama client for communicating with Ollama AI models."""
from typing import Optional

from ollama import Client

from taskuccino.config import ModelsConfig


class OllamaClient:
    """Client for interacting with Ollama AI models."""

    def __init__(self, api_url: str, models: Optional[ModelsConfig]):
        self.api_url = api_url
        self.models = models
        self.client = Client(host=api_url)

    def _get_model_for_capability(self, capability: str = "tools") -> str:
        """Return the name of a model that has the specified capability."""
        if self.models is None:
            list_response = self.client.list()
            all_models = list_response.models  # pylint: disable=no-member
            for model in all_models:
                if model.model is not None:
                    model_info = self.client.show(model.model)
                    if model_info.capabilities is not None:
                        if capability in model_info.capabilities:
                            return model.model
        else:
            if (
                self.models.primary_model
                and capability in self.models.primary_model.capabilities
            ):
                return self.models.primary_model.name
            for model in self.models.backup_models:
                if capability in model.capabilities:
                    return model.name
        raise RuntimeError(f"No model found with capability: {capability}")

    def chat(self, messages: list) -> object:
        """Send a chat request to the Ollama model."""
        model = self._get_model_for_capability()
        print(f'Using model {model} to fulfil chat request {messages[-1]["content"]}')
        return self.client.chat(model=model, messages=messages)

    def generate(self, prompt: str, images: Optional[list] = None) -> object:
        """Generate a response using the Ollama model."""
        model = self._get_model_for_capability(
            images is not None and len(images) > 0 and "vision" or "tools"
        )
        print(f"Using model {model} to fulfil generate request {prompt}")
        return self.client.generate(model=model, prompt=prompt, images=images)
