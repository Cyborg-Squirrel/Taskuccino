from typing import Optional

import discord
from discord.ext import commands, tasks

import config
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

@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord"""
    print(f"{bot.user} has connected to Discord!")
    print(f"Bot is in {len(bot.guilds)} guild(s)")


async def on_bot_mentioned(message: discord.Message):
    """Called when the bot is mentioned in a message"""
    if remindme_config.react_to_messages:
        reaction_emoji = remindme_config.reaction_emoji
        await message.add_reaction(reaction_emoji)

    # Processing attachments can take awhile.
    # Don't set the bot to "typing" until after we've processed the attachments.
    image_descriptions = ""
    attachment_number = 1
    image_attachments = [
        a
        for a in message.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]

    if len(image_attachments) > 0:
        await message.reply(f"Give me a moment to look at what you sent")

    for image_attachment in image_attachments:
        if image_attachment.content_type and image_attachment.content_type.startswith(
            "image/"
        ):
            image_bytes = await image_attachment.read()
            image_description = await ollama_client.generate(
                prompt="Describe this image", images=[image_bytes]
            )
            image_descriptions += (
                f"Image {attachment_number}: {image_description.response}\n"
            )
            attachment_number += 1

    async with message.channel.typing():
        response = await ollama_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": f"The user attached: {image_descriptions}",
                },
                {"role": "user", "content": message.content},
            ]
        )

    if response.message.content is not None:
        # Discord has a max message length of 2000 characters, split the message up if needed
        start = 0
        end = 2000 if len(response.message.content) > 2000 else len(response.message.content) - 1
        first_chunk = True
        while end < len(response.message.content):
            if first_chunk:
                await message.reply(response.message.content[start:end])
                first_chunk = False
            else:
                await message.channel.send(response.message.content[start:end])
            start = end
            if end + 2000 < len(response.message.content):
                end += 2000
            elif end == len(response.message.content) - 1:
                break
            else:
                end = len(response.message.content) - 1


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
        bot.run(token)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord token")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
