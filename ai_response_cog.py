"""Background message response cog for Discord bot."""
import multiprocessing as mp

from discord.ext import commands, tasks


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
        message = None
        for message in self.bot.cached_messages:
            if message.id == ollama_response.request.message_id:
                break
        if message is not None:
            # Discord has a max message length of 2000 characters, split the message up if needed
            start = 0
            end = (
                2000
                if len(ollama_response.content) > 2000
                else len(ollama_response.content) - 1
            )
            first_chunk = True
            while end < len(ollama_response.content):
                if first_chunk:
                    await message.reply(ollama_response.content[start:end])
                    first_chunk = False
                else:
                    await message.channel.send(ollama_response.content[start:end])
                start = end
                if end + 2000 < len(ollama_response.content):
                    end += 2000
                elif end == len(ollama_response.content) - 1:
                    break
                else:
                    end = len(ollama_response.content) - 1
