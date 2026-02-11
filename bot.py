import multiprocessing as mp
from dataclasses import dataclass
from time import sleep
from typing import Optional

import discord
from discord.ext import commands, tasks
from ollama import ChatResponse

import config
from ai_response_cog import AiResponseCog
from ollama_client import OllamaClient

intents = discord.Intents.default()
intents.message_content = True

remindme_config = config.load_config()
bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    description="Nothing to see here!",
    intents=intents,
)
ollama_client = OllamaClient(
    api_url=remindme_config.api_url, models=remindme_config.models
)


@dataclass
class OllamaRequest:
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
    content: str
    request: OllamaRequest

    def __init__(self, content: str, request: OllamaRequest):
        self.content = content
        self.request = request


ollama_request_queue = mp.Queue()
ollama_response_queue = mp.Queue()


def ollama_background_task(request_queue: mp.Queue, response_queue: mp.Queue):
    print("Starting Ollama background task")
    while True:
        if request_queue.empty():
            sleep(5)
            continue

        ollama_request = request_queue.get_nowait()
        if ollama_request is None:
            sleep(5)
            continue

        image_descriptions = ""
        attachment_number = 1
        chat_response: ChatResponse
        messages = [
            {
                "role": "system",
                "content": f"""
                You are a Discord bot. 
                Text formatting is supported but you can only use bold, italics, 
                underline, strikethrough, code blocks, and inline code.
                Do not use any other markdown syntax as it will not render properly.""",
            }
        ]
        if ollama_request.image_attachments:
            for attachment in ollama_request.image_attachments:
                image_description = ollama_client.generate(
                    prompt="Describe this image", images=[attachment]
                )
                image_descriptions += (
                    f"Image {attachment_number}: {image_description.response}\n"
                )
                attachment_number += 1

            messages.append(
                {
                    "role": "system",
                    "content": f"The user attached: {image_descriptions}",
                }
            )

        messages.append({"role": "user", "content": ollama_request.content})
        chat_response = ollama_client.chat(messages=messages)
        response_content = (
            chat_response.message.content
            if chat_response.message.content is not None
            else ""
        )
        ollama_response = OllamaResponse(
            content=response_content, request=ollama_request
        )
        response_queue.put(ollama_response)


@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord"""
    print(f"{bot.user} has connected to Discord!")
    print(f"Bot is in {len(bot.guilds)} guild(s)")
    await bot.add_cog(AiResponseCog(bot, ollama_response_queue))


async def on_bot_mentioned(message: discord.Message):
    """Called when the bot is mentioned in a message"""
    if not isinstance(message.channel, discord.abc.Messageable):
        print(f"Channel {message.channel} is not messageable, cannot respond")
        return
    if remindme_config.react_to_messages:
        reaction_emoji = remindme_config.reaction_emoji
        await message.add_reaction(reaction_emoji)

    image_attachments = [
        a
        for a in message.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]
    image_attachment_bytes = []

    if len(image_attachments) > 0:
        await message.reply(f"Give me a moment to look at what you sent")

    for image_attachment in image_attachments:
        if image_attachment.content_type and image_attachment.content_type.startswith(
            "image/"
        ):
            image_bytes = await image_attachment.read()
            image_attachment_bytes.append(image_bytes)

    ollama_request = OllamaRequest(
        channel_id=message.channel.id,
        message_id=message.id,
        content=message.content,
        image_attachments=image_attachment_bytes,
    )
    ollama_request_queue.put(ollama_request)


@bot.event
async def on_message(message):
    """Called when any message is sent where the bot has access"""
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        # await on_bot_mentioned(message)
        bot.loop.create_task(on_bot_mentioned(message))
        return

    if isinstance(message.channel, discord.TextChannel):
        bot_mentioned = [user for user in message.mentions if user == bot.user]
        if bot_mentioned:
            await on_bot_mentioned(message)


@bot.tree.command()
@discord.app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    user = member or interaction.user
    assert isinstance(user, discord.Member)
    if user.joined_at is None:
        await interaction.response.send_message(f"{user} has no join date.")
    else:
        await interaction.response.send_message(
            f"{user} joined {discord.utils.format_dt(user.joined_at)}"
        )


def main():
    """Main entry point"""
    token = remindme_config.token

    if remindme_config.token is None or remindme_config.token == "":
        raise ValueError(
            "Discord token is required in config.json. Please update the config file with your bot token."
        )

    try:
        p1 = mp.Process(
            name="ollama_thread",
            target=ollama_background_task,
            args=(ollama_request_queue, ollama_response_queue),
        )
        p1.start()
        bot.run(token)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord token")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
