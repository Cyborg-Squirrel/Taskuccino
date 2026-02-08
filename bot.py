import discord
from discord.ext import commands

import config
from ollama_client import OllamaClient

intents = discord.Intents.default()
intents.message_content = True

remindme_config = config.load_config()
bot = commands.Bot(command_prefix=commands.when_mentioned, description='Nothing to see here!', intents=intents)
ollama_client: OllamaClient

@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')

@bot.event
async def on_message(message):
    """Called when any message is sent where the bot has access"""
    if message.author == bot.user:
        return
    
    if isinstance(message.channel, discord.DMChannel):
        if remindme_config.react_to_messages:
            reaction_emoji = remindme_config.reaction_emoji
            await message.add_reaction(reaction_emoji)

        response = ollama_client.chat(messages=[{"role": "user", "content": message.content}])
        await message.reply(response.message.content)
        return
    
    if isinstance(message.channel, discord.TextChannel):
        bot_mentioned = [user for user in message.mentions if user == bot.user]
        if bot_mentioned:
            if remindme_config.react_to_messages:
                reaction_emoji = remindme_config.reaction_emoji
                await message.add_reaction(reaction_emoji)
            await message.reply("Hello! {}".format(message.author))
    
    await bot.process_commands(message)

@bot.command(name='hello')
async def hello(ctx):
    """Simple hello command"""
    await ctx.send(f'Hello {ctx.author.name}!')

def main():
    """Main entry point"""
    token = remindme_config.token
    ollama_client = OllamaClient(api_url=remindme_config.api_url, models=remindme_config.models)

    if not token:
        print('Error: DISCORD_TOKEN not found in config')
        print('Please update config.json with your Discord bot token')
        return
    
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print('Error: Invalid Discord token')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
