from typing import Optional

from ollama import ChatResponse, Client, ListResponse, ShowResponse

from config import ModelsConfig


class OllamaClient():
    def __init__(self, api_url:str, models:Optional[ModelsConfig]):
        self.api_url = api_url
        self.models = models
        self.client = Client(host=api_url)

    def _get_model_for_capability(self, capability:str="tools") -> str:
        """Return the name of a model that has the specified capability."""
        if self.models is None:
            all_models = self.client.list().models
            for model in all_models:
                if model.model is not None:
                    model_info = self.client.show(model.model)
                    if model_info.capabilities is not None:
                        if capability in model_info.capabilities:
                            return model.model
        else:
            if self.models.primary_model and capability in self.models.primary_model.capabilities:
                return self.models.primary_model.name
            for model in self.models.backup_models:
                if capability in model.capabilities:
                    return model.name
        raise RuntimeError(f'No model found with capability: {capability}')

    def chat(self, messages:list):
        ollama_response = self.client.chat(model=self._get_model_for_capability(), messages=messages)
        return ollama_response