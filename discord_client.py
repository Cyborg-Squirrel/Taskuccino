import multiprocessing as mp
from queue import Empty
from typing import Optional

import discord
from discord.ext import commands, tasks


class CommandClient(discord.Client):
    user: discord.ClientUser
    guilds: list[int] = []
    output_queue: mp.Queue

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    def setup(self, output_queue: mp.Queue):
        self.output_queue = output_queue

    async def sync_guild(self, guildId: int):
        """Add a guild to the command tree for syncing."""
        if self.is_ready():
            guild = self.get_guild(guildId)
            if guild is not None:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
        else:
            print(f"Client isn't ready, queueing guild for sync")
            self.guilds.append(guildId)

    async def sync(self):
        guilds_list = self.guilds.copy()
        for guild in guilds_list:
            await self.sync_guild(guild)
            self.guilds.remove(guild)


class MyCog(commands.Cog):
    input_queue: Optional[mp.Queue] = None

    def __init__(self, client: CommandClient):
        self.client = client

    async def start(self) -> None:
        self.sync_loop.start()

    @tasks.loop(seconds=15.0)
    async def sync_loop(self):
        if self.input_queue is not None:
            try:
                guildId = self.input_queue.get_nowait()
                if isinstance(guildId, int):
                    await self.client.sync_guild(guildId)
            except Empty:
                pass
        await self.client.sync()


client = CommandClient(intents=discord.Intents.default())
cog = MyCog(client)


@client.event
async def on_ready():
    """Called when the client has successfully connected to Discord"""
    await cog.start()


@client.tree.command()
@discord.app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    pass
    # user = member or interaction.user
    # assert isinstance(user, discord.Member)
    # if user.joined_at is None:
    #     await interaction.response.send_message(f"{user} has no join date.")
    # else:
    #     await interaction.response.send_message(
    #         f"{user} joined {discord.utils.format_dt(user.joined_at)}"
    #     )


def run_client(token: str, input_queue: mp.Queue, output_queue: mp.Queue):
    cog.input_queue = input_queue
    client.setup(output_queue)
    client.run(token)
