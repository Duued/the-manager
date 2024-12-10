import datetime
import os
import re
from typing import Optional, Union

import asyncpg
import discord
import dotenv
import mystbin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands


# from . import beta


filtered_regexes = [
    r"f(a|@)g",
    r"\.gg/.*",
    r"https://discord\.com/invite/\S*.",
    r"n(i|!)gg",
    r"r(a|@)p(e|3)",
    r"p(o|r|0|\*)(r|o|0|\*)n",
    r"l(o|0|\*)(l|1)(i|!)",
    r"ky(s|$)",
    r"keep(\s)?yourself(\s)?safe",
]

curse_filtered_regexes = [
    r"f(u|\*)(c|\*|k)(c|\*|k)",
    r"(a|@)(s|$|\*)(s|$|\*)",
    r"d(i|!)(c|\*)(k|c|\*)",
    r"pu(s|\*|\$)(s|\*|\$)y",
    r"b(a|@)(s|$)(t|\+)(a|@)rd",
]

adult_filtered_regexes = [
    r"s(e|3|\*)x",
    r"p(o|r|0|\*)(r|o|0|\*)n",
    r"nud(e|3)",
    r"d(i|!)(c|\*)(k|c|\*)",
    r"pu(s|\*|\$)(s|\*|\$)y",
    r"c(o|0|\*)(c|k)(c|k)",
]


def filter_message(message: str) -> bool:
    """Filter message. If if filtered (true), prohibit sending."""
    for regex in filtered_regexes:
        results = re.search(regex, message, re.IGNORECASE)
        if results:
            return True
    return False


def curse_filter_message(message: str) -> bool:
    """Filter message with the curse filtered regexes.
    Prohibit sending if true."""
    for regex in curse_filtered_regexes:
        results = re.search(regex, message, re.IGNORECASE)
        if results:
            return True
    return False


def adult_filter_message(message: str) -> bool:
    """Filter message with the curse filtered regexes.
    Prohibit sending if true."""
    for regex in adult_filtered_regexes:
        results = re.search(regex, message, re.IGNORECASE)
        if results:
            return True
    return False


def to_bool(input: Union[str, bool]) -> bool:
    if isinstance(input, str):
        lowered = input.lower()
        if lowered in ("yes", "y", "true", "t", "1", "on", "allow"):
            return True
        elif lowered in ("no", "n", "false", "f", "0", "off", "deny"):
            return False
        else:
            return
    else:
        return input


dotenv.load_dotenv(verbose=True)


class PhoneConnection:
    def __init__(
        self,
        channel1: discord.TextChannel,
        channel2: discord.TextChannel,
        id: int,
        webhook: discord.Webhook = None,
        mb_client: mystbin.Client = None,
        bot: commands.Bot = None,
    ):
        self.channel1 = channel1
        self.channel2 = channel2
        self.id = id
        self.webhook = webhook
        self.mb_client = mb_client
        self.to_log = ""
        self.bot = bot
        self.call_id: int

    async def connect(self):
        description = "Be civil and respectful. For user safety, these calls are logged and messages are filtered."
        embed = discord.Embed(
            title=f"Connected to {self.channel2.name}",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )
        await self.channel1.send(embed=embed)
        embed.title = f"Connected to {self.channel1.name}"
        await self.channel2.send(embed=embed)
        connections.append(self)
        num = len(await self.bot.db.fetch("SELECT * FROM calls"))
        await self.bot.db.execute(
            """INSERT INTO calls(server_one_id, channel_one_id, server_two_id, channel_two_id, id)
                                VALUES($1, $2, $3, $4, $5)""",
            self.channel1.guild.id,
            self.channel1.id,
            self.channel2.guild.id,
            self.channel2.id,
            num + 1,
        )
        self.call_id = num + 1

    async def close(self, reason: str = "This call has been disconnected."):
        embed = discord.Embed(
            title="Disconnected!",
            description=reason,
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        await self.channel1.send(embed=embed)
        if self.channel1.id != self.channel2.id:
            await self.channel2.send(embed=embed)
        paste = None

        content = f"""
Conversation from {self.channel1.name} ({self.channel1.id})
Guild1: {self.channel1.guild.name} ({self.channel1.guild.id}) 

{self.channel2.name} ({self.channel2.id}) 
Guild2: {self.channel2.guild.name} ({self.channel2.guild.id}) has ended.
        
{f'[View Logs](<{paste}>)' if paste else ''}"""
        await self.webhook.send(content)

    async def send(self, message: discord.Message):
        if message.content == "":
            return
        if message.channel.id == self.channel1.id:
            channel = self.channel2
        elif message.channel.id == self.channel2.id:
            channel = self.channel1
        else:
            return
        filtered = filter_message(message.content)
        filtered_message = ""
        if filtered:
            filtered_message += "This message violates the phone system's content filter (DevPolicy).\n"
        guild1_filter_settings: asyncpg.Record | None = await self.bot.db.fetchrow(
            "SELECT * FROM call_config WHERE guild_id=$1", self.channel1.guild.id
        )
        guild2_filter_settings: asyncpg.Record | None = await self.bot.db.fetchrow(
            "SELECT * FROM call_config WHERE guild_id=$1", self.channel2.guild.id
        )
        if guild1_filter_settings:
            if guild1_filter_settings["swears_allowed"] is False:  # Do filter
                filtered = curse_filter_message(message.content)
                if filtered:
                    filtered_message += "This message violates the cursing content policy of one or both guilds.\n"

            if guild1_filter_settings["adult_allowed"] is False:  # Do filter
                filtered = adult_filter_message(message.content)
                if filtered:
                    filtered_message += "This message violates the adult content policy of one or both guilds.\n"
        if filtered_message == "" and guild2_filter_settings:
            if guild2_filter_settings["swears_allowed"] is False:  # Do filter
                filtered = curse_filter_message(message.content)
                if filtered:
                    filtered_message += "This message violates the cursing content policy of one or both guilds.\n"
            if guild2_filter_settings["adult_allowed"] is False:  # Do filter
                filtered = adult_filter_message(message.content)
                if filtered:
                    filtered_message += "This message violates the adult content policy of one or both guilds.\n"

        if filtered_message == "":  # Send as there was no filtering done.
            self.to_log += f"Message from: AUTHOR: {message.author.name} ({message.author.id}) GUILD: {message.guild.name} ({message.guild.id}) CONTENT: {message.content}\n"
            embed = discord.Embed(
                title="Incoming Message!",
                description=message.content,
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(),
            )
            embed.set_author(name=message.author.name, icon_url=message.author.display_avatar)
            embed.set_footer(text=f"Sent from {message.author.name} (ID: {message.author.id})")
            await channel.send(embed=embed)
            await self.bot.db.execute(
                """INSERT INTO messages(id, call_id, content, author_id, channel_id, guild_id, filtered)
                                    VALUES($1, $2, $3, $4, $5, $6, $7)""",
                message.id,
                self.call_id,
                message.content,
                message.author.id,
                message.channel.id,
                message.guild.id,
                False,
            )
        else:  # Filtered message, don't send and alert author.
            filtered_message += "Your message has not been sent."
            embed = discord.Embed(
                title="Message not sent!",
                description=filtered_message,
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            await message.reply(embed=embed, mention_author=False)
            await self.bot.db.execute(
                """INSERT INTO messages(id, call_id, content, author_id, channel_id, guild_id, filtered)
                                    VALUES($1, $2, $3, $4, $5, $6, $7)""",
                message.id,
                self.call_id,
                message.content,
                message.author.id,
                message.channel.id,
                message.guild.id,
                True,
            )


connections: list[PhoneConnection] = []
pending_channels: list[discord.TextChannel] = []


async def create_connections(
    logging_hook: Optional[discord.Webhook] = None, mb_client: mystbin.Client = None, bot: commands.Bot = None
):
    if len(pending_channels) % 2 == 0:
        connection = PhoneConnection(
            pending_channels.pop(0), pending_channels.pop(0), len(connections) + 1, logging_hook, mb_client, bot
        )
        await connection.connect()
        if logging_hook:
            await logging_hook.send(
                f"Connection created! {connection.channel1.name} ({connection.channel1.id}) -> {connection.channel2.name} ({connection.channel2.id})"
            )


class Phone(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook = discord.Webhook.from_url(url=os.getenv("phone_hook"), client=bot)
        self.mb_client = mystbin.Client(token=os.getenv("MYSTBIN_API_KEY"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        for connection in connections:
            if connection.channel1.id == message.channel.id or connection.channel2.id == message.channel.id:
                await connection.send(message)

    @app_commands.command(name="phone-config", description="Configure the phone system for the current guild.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(setting="The setting to modify", value="The new value of the setting.")
    @app_commands.choices(
        setting=[
            Choice(name="Allow adult content", value="adult_allowed"),
            Choice(name="Allow curse words", value="swears_allowed"),
        ]
    )
    @app_commands.choices(value=[Choice(name="Allow", value="True"), Choice(name="Deny", value="False")])
    async def configure_guild_phone(
        self, interaction: discord.Interaction, setting: Choice[str] = None, value: Choice[str] = None
    ):
        if setting and value:
            configuration = {"config_key": setting.value, "set_value": value.value}
            await self.bot.db.execute(
                f"""INSERT INTO call_config(guild_id, {configuration['config_key']})
                                VALUES ($1, $2)

                                ON CONFLICT(guild_id) DO UPDATE
                                SET {configuration['config_key']} = $2""",
                interaction.guild.id,
                to_bool(configuration["set_value"]),
            )
        data = await self.bot.db.fetchrow("SELECT * FROM call_config WHERE guild_id=$1", interaction.guild.id)
        if data is None:
            return await interaction.response.send_message(
                "There is no phone system configuration for this guild. Create some first!", ephemeral=True
            )
        embed = discord.Embed(
            title="Phone System configuration",
            description=f"Phone system cursing allowed?: {data['swears_allowed']}\nPhone system adult content allowed? {data['adult_allowed']}",
            color=0x7289DA,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    phone = app_commands.Group(name="phone", description="The phone management commands", guild_only=True)

    @phone.command(name="connect", description="Starts a phone connection")
    # @beta.is_beta_i()
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def create_phone_connection(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Connecting...",
            description="Please wait... Searching for avaliable connections to make.",
            color=0x7289DA,
            timestamp=datetime.datetime.now(),
        )
        if len(connections) != 0:
            for connection in connections:
                if connection.channel1.id == interaction.channel.id or connection.channel2.id == interaction.channel.id:
                    return await interaction.response.send_message("There is already a running connection in this channel.")

        if len(pending_channels) != 0:
            for pending_channel in pending_channels:
                if pending_channel.id == interaction.channel.id:
                    return await interaction.response.send_message("This channel is already waiting to connect.")
        embed.add_field(
            name="Report?",
            value="Want to report a call? `/phone disconnect` and then join the support server and open a ticket.",
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
        pending_channels.append(interaction.channel)
        await interaction.response.send_message(embed=embed)
        await self.webhook.send(
            f"Attempting to create connection for {interaction.channel.name} ({interaction.channel.id})\nGuild {interaction.guild.name} ({interaction.guild.id})"
        )
        await create_connections(self.webhook, self.mb_client, self.bot)

    @phone.command(name="disconnect", description="Hangs up your current connection")
    # @beta.is_beta_i()
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def disconnect_phone_connection(self, interaction: discord.Interaction):
        for connection in connections:
            if connection.channel1.id == interaction.channel.id or connection.channel2.id == interaction.channel.id:
                await connection.close()
                del connections[connection.id - 1]
                return await interaction.response.send_message("Connection successfully closed")
        await interaction.response.send_message("No active connection to close!", ephemeral=True)

    @phone.command(name="cancel", description="Removes you from the waiting queue.")
    # @beta.is_beta_i()
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def cancel_phone_connection(self, interaction: discord.Interaction):
        try:
            index = pending_channels.index(interaction.channel)
            msg = "You have been removed from the queue."
            ephemeral = False
            del pending_channels[index]
        except ValueError:
            index = None
            msg = "You cannot be removed from the queue, you weren't in it."
            ephemeral = True

        await interaction.response.send_message(msg, ephemeral=ephemeral)

    @commands.group(name="connections", brief="Manages phone connections.", invoke_without_command=True)
    @commands.is_owner()
    async def connection_management(self, ctx: commands.Context):
        text = ""
        if len(connections) != 0:
            for connection in connections:
                text += f"""
Active Connection -> ID: {connection.id} 
- CHANNEL1: {connection.channel1.name} ({connection.channel1.id}) 
- GUILD1: {connection.channel1.guild.name} ({connection.channel1.guild.id}) 

- CHANNEL2: {connection.channel2.name} ({connection.channel2.id}) 
- GUILD2: {connection.channel2.guild.name} ({connection.channel2.guild.id})\n"""

            if len(text) > 1000:
                paste = await self.mb_client.create_paste(filename="connections.txt", content=text)
                text = f"Too large to send in embed.\n[View Paste]({paste})"
        else:
            text = "No active connections"
        embed = discord.Embed(
            title="Active Connections", description=text, color=0x7289DA, timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)

    @connection_management.command(name="close", brief="Force closes an active connection.")
    @commands.is_owner()
    async def force_close_active_connection(self, ctx: commands.Context, id: int, *, reason: str = None):
        reason = f"This connection was closed by the developer. {f'Reason: {reason}' if reason else 'No reason provided.'}"
        connection = discord.utils.get(connections, id=id)
        if connection:
            await connection.close(reason)
            msg = f"Connection **{id}** was successfully closed."
        else:
            msg = f"Connection **{id}** was not found."

        await ctx.send(msg)

    @connection_management.command(name="clearpending", brief="Clears pending connections", aliases=["clearp", "cpending"])
    @commands.is_owner()
    async def clear_pending_connections(self, ctx: commands.Context):
        for channel in pending_channels:
            await channel.send("You have been removed from the pending queue.")
        pending_channels.clear()

    @connection_management.command(name="closeall", brief="Force closes all active connections.")
    @commands.is_owner()
    async def close_all_connections(self, ctx: commands.Context, *, reason: str = None):
        reason = f"This call was closed by the developer. {f'Reason: {reason}' if reason else 'No reason provided.'}"
        if len(connections) != 0:
            for connection in connections:
                await connection.close(reason)
                msg = "All connections closed."
        else:
            msg = "No connections to close."
        await ctx.send(msg)

    @connection_management.command(name="clear", brief="Closes all connections, and clears queues.")
    @commands.is_owner()
    async def clear_all(self, ctx: commands.Context, *, reason: str = None):
        reason = f"This call was closed by the developer. {'Reason:' if reason else ''}"
        pending_channels.clear()
        for connection in connections:
            await connection.close(reason)
            msg = "All connections closed. `pending_channels` reset"
        else:
            msg = "No connections to close. `pending_channels` reset"
        await ctx.send(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Phone(bot))
