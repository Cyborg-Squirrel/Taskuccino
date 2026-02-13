"""Background message response cog for Discord bot."""
import multiprocessing as mp

from discord.ext import commands, tasks

from _types import OllamaError, OllamaResponse


class AiResponseCog(commands.Cog):
    """Background cog for handling the response queue."""

    def __init__(self, bot: commands.Bot, queue: mp.Queue):
        self.bot = bot
        self.queue = queue

    async def cog_load(self):
        """Start the background task when the cog is loaded."""
        self.my_task.start()

    async def cog_unload(self):
        """Stop the background task when the cog is unloaded."""
        self.my_task.stop()

    @tasks.loop(seconds=5)
    async def my_task(self):
        """Background task that processes AI responses from the queue."""
        if self.queue.empty():
            return
        ollama_response = self.queue.get_nowait()
        ollama_response_message = ''
        if ollama_response.isinstance(OllamaResponse):
            ollama_response_message = ollama_response.content
        elif ollama_response.isinstance(OllamaError):
            ollama_response_message = ollama_response.error

        message = None
        for message in self.bot.cached_messages:
            if message.id == ollama_response.request.message_id:
                break
        if message is not None:
            # Discord has a max message length of 2000 characters, split the message up if needed
            start = 0
            end = (
                2000
                if len(ollama_response_message) > 2000
                else len(ollama_response_message) - 1
            )
            first_chunk = True
            while end < len(ollama_response_message):
                if first_chunk:
                    await message.reply(ollama_response_message[start:end])
                    first_chunk = False
                else:
                    await message.channel.send(ollama_response_message[start:end])
                start = end
                if end + 2000 < len(ollama_response_message):
                    end += 2000
                elif end == len(ollama_response_message) - 1:
                    break
                else:
                    end = len(ollama_response_message) - 1
