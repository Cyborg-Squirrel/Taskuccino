"""AI response cog for Discord bot."""
import multiprocessing as mp

from discord.ext import commands, tasks


class AiResponseCog(commands.Cog):
    """Cog for handling AI-generated responses from Ollama."""

    def __init__(self, bot: commands.Bot, queue: mp.Queue):
        self.bot = bot
        self.queue = queue

    async def cog_load(self):
        self.my_task.start()

    async def cog_unload(self):
        self.my_task.stop()

    @tasks.loop(seconds=5)
    async def my_task(self):
        """Background task that processes AI responses from the queue."""
        if self.queue.empty():
            return
        ollama_response = self.queue.get_nowait()
        request_message = ollama_response.request.message
        message = None
        for message in self.bot.cached_messages:
            if message.id == request_message.message_id:
                break
        if message is not None:
            # Discord has a max message length of 2000 characters, split if needed
            start = 0
            end = (
                2000
                if len(ollama_response.content) > 2000
                else len(ollama_response.content)
            )
            while start < len(ollama_response.content):
                await message.reply(ollama_response.content[start:end])
                start = end
                end = start + 2000
