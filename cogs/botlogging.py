import datetime
from typing import Union

import aiohttp
import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

import hooks


class WateredDownInfoEmbed(discord.Embed):
    def __init__(self, bot: commands.Bot, guild: discord.Guild, left: bool):
        super().__init__()
        self.color = 0x7289DA
        created_at = guild.created_at
        created_at_string = None
        if not left:
            created_at_string = f'\nGuild Created At: {discord.utils.format_dt(created_at, "f")} ({discord.utils.format_dt(created_at, "R")})'
        self.description = f"""
        Guild Count: {len(bot.guilds)}

        Guild Name: {guild.name}

        Guild ID: {guild.id}

        Guild Owner: {guild.owner.mention} ({guild.owner.id})
        {created_at_string}"""


class BotLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.Pool = bot.db

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        embed = WateredDownInfoEmbed(self.bot, guild, False)
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hooks.guildhook, session=session)
            await webhook.send(content="Guild Joined", embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        embed = WateredDownInfoEmbed(self.bot, guild, True)
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hooks.guildhook, session=session)
            await webhook.send(content="Guild Removed", embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        await self.db.execute(
            """INSERT INTO command_logs(author_id, channel_id, guild_id, command, timestamp, type)
                                VALUES ($1, $2, $3, $4, $5, $6)""",
            ctx.author.id,
            ctx.channel.id,
            ctx.guild.id if ctx.guild else 0,
            ctx.command.qualified_name,
            datetime.datetime.utcnow(),
            "text",
        )

    @commands.Cog.listener()
    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: Union[app_commands.Command, app_commands.ContextMenu]
    ):
        if isinstance(command, app_commands.Command):
            type = "app_command"
        else:
            type = "context menu"
        await self.db.execute(
            """INSERT INTO command_logs(author_id, channel_id, guild_id, command, timestamp, type)
                                VALUES ($1, $2, $3, $4, $5, $6)""",
            interaction.user.id,
            interaction.channel.id,
            interaction.guild.id if interaction.guild else 0,
            interaction.command.qualified_name,
            datetime.datetime.utcnow(),
            type,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(BotLogger(bot))
