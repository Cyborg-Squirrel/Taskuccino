"""A Discord chat bot powered by AI"""

import multiprocessing as mp
from time import sleep
from typing import Optional

import discord
from discord.ext import commands
from ollama import ChatResponse

from taskuccino import (AiResponseCog, OllamaClient, load_config,
                        load_system_prompt)
from taskuccino._types import OllamaError, OllamaRequest, OllamaResponse

intents = discord.Intents.default()
intents.message_content = True

system_prompt = load_system_prompt()
bot_config = load_config()
bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    description="Nothing to see here!",
    intents=intents,
)
ollama_client = OllamaClient(api_url=bot_config.api_url, models=bot_config.models)

ollama_request_queue = mp.Queue()
ollama_response_queue = mp.Queue()


def ollama_background_task(request_queue: mp.Queue, response_queue: mp.Queue):
    """
    Background task that processes requests from the request_queue using the
    Ollama client and puts responses in the response_queue.
    """
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
        messages = [{"role": "system", "content": system_prompt}]
        if ollama_request.image_attachments:
            for attachment in ollama_request.image_attachments:
                try:
                    image_description = ollama_client.generate(
                        prompt="Describe this image", images=[attachment]
                    )
                    img_response = (
                        image_description.response # pylint: disable=no-member
                    )
                    image_descriptions += f"Image {attachment_number}: {img_response}\n"
                    attachment_number += 1
                except Exception as e: # pylint: disable=broad-exception-caught
                    error_response = OllamaError(e, ollama_request)
                    response_queue.put(error_response)
                    return

            messages.append(
                {
                    "role": "system",
                    "content": f"""The user attached an image with the following
                     description: {image_descriptions}""",
                }
            )

        messages.append({"role": "user", "content": ollama_request.content})
        try:
            chat_response = ollama_client.chat(messages=messages)
            message_content = chat_response.message.content  # pylint: disable=no-member
            response_content = message_content if message_content is not None else ""
            ollama_response = OllamaResponse(
                content=response_content, request=ollama_request
            )
            response_queue.put(ollama_response)
        except Exception as e: # pylint: disable=broad-exception-caught
            error_response = OllamaError(e, ollama_request)
            response_queue.put(error_response)
            return


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
    if bot_config.react_to_messages:
        reaction_emoji = bot_config.reaction_emoji
        await message.add_reaction(reaction_emoji)

    image_attachments = [
        a
        for a in message.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]
    image_attachment_bytes = []

    if len(image_attachments) > 0:
        await message.reply("Give me a moment to look at what you sent")

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
    member="""
    The member you want to get the joined date from.
    This defaults to the user who uses the command"""
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
    token = bot_config.token

    if bot_config.token is None or bot_config.token == "":
        raise ValueError(
            "Discord token is required in config.json."
            "Please update the config file with your bot token."
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


if __name__ == "__main__":
    main()
