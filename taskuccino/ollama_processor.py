import multiprocessing as mp
import threading
from time import sleep

from taskuccino._types import OllamaError, OllamaResponse
from taskuccino.ollama_client import OllamaClient


class OllamaProcessor:  # pylint: disable=too-few-public-methods
    """Background task processor for Ollama requests."""

    request_queue: mp.Queue
    response_queue: mp.Queue
    system_prompt: str
    ollama_client: OllamaClient

    def __init__(
        self,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
        system_prompt: str,
        ollama_client: OllamaClient,
    ):
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.system_prompt = system_prompt
        self.ollama_client = ollama_client

    def start(self) -> threading.Thread:
        t = threading.Thread(target=self._process_messages)
        t.start()
        return t

    def _process_images(self, request_message):
        """Process image attachments and return descriptions."""
        image_descriptions = ""
        attachment_number = 1
        image_attachments = request_message.image_attachments

        if image_attachments is None or len(image_attachments) == 0:
            return image_descriptions

        for attachment in image_attachments:
            image_description = self.ollama_client.generate(
                prompt="Describe this image", images=[attachment]
            )
            img_response = (
                image_description.response  # pylint: disable=no-member
            )
            image_descriptions += f"Image {attachment_number}: {img_response}\n"
            attachment_number += 1

        return image_descriptions

    def _process_messages(self):
        """
        Background task that processes requests from the request_queue using the
        Ollama client and puts responses in the response_queue.
        """
        while True:
            if self.request_queue.empty():
                sleep(5)
                continue

            ollama_request = self.request_queue.get_nowait()
            if ollama_request is None:
                sleep(5)
                continue

            try:
                messages = [{"role": "system", "content": self.system_prompt}]
                request_message = ollama_request.message

                for history_message in ollama_request.history:
                    messages.append(
                        {
                            "role": history_message.role.value,
                            "content": history_message.content,
                        }
                    )

                image_descriptions = self._process_images(request_message)
                if image_descriptions:
                    messages.append(
                        {
                            "role": "system",
                            "content": f"""The user attached an image with the following
                             description: {image_descriptions}""",
                        }
                    )

                messages.append(
                    {"role": "user", "content": request_message.content}
                )
                chat_response = self.ollama_client.chat(messages=messages)
                message_content = chat_response.message.content
                response_content = (
                    message_content if message_content is not None else ""
                )
                ollama_response = OllamaResponse(
                    content=response_content, request=ollama_request
                )
                self.response_queue.put(ollama_response)
            except Exception as e:  # pylint: disable=broad-exception-caught
                error_response = OllamaError(str(e), ollama_request, e)
                self.response_queue.put(error_response)
