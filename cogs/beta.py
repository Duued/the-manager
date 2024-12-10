import datetime

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


async def check_beta_status(*, db: asyncpg.pool.Pool, guild_id: int) -> bool | None:
    return await db.fetchval("SELECT active FROM beta WHERE guildid=$1", guild_id)


def is_beta():
    """Ensures the guild is a beta guild."""

    async def check(ctx: commands.Context):
        if ctx.guild is not None:
            status = await check_beta_status(db=ctx.bot.db, guild_id=ctx.guild.id)
            if status:
                return True
        raise commands.CheckFailure(
            "Must be ran in a beta enabled guild. Open a ticket in the support (</support:1129509610424897597>) server to enable beta!"
        )

    return commands.check(check)


def is_beta_i():
    """Ensures the guild is a beta guild.

    The exact same as is_beta but for interactions."""

    async def check(interaction: discord.Interaction):
        if interaction.guild is not None:
            status = await check_beta_status(db=interaction.client.db, guild_id=interaction.guild.id)
            if status:
                return True
        raise app_commands.CheckFailure(
            "Must be ran in a beta enabled guild. Open a ticket in the support (</support:1129509610424897597>) server to enable beta!"
        )

    return app_commands.check(check)


class Beta(commands.Cog):
    """The beta program management commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @commands.group(name="beta", invoke_without_command=True, brief="Beta checking and management commands.")
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def beta_group(self, ctx: commands.Context, *, guild: discord.Guild = commands.CurrentGuild):
        if guild != ctx.guild:
            if not await ctx.bot.is_owner(ctx.author):
                raise commands.CheckFailure("Unauthorized. You can only check the current guild beta status.")
            else:
                status = await check_beta_status(db=self.db, guild_id=guild.id)
        else:
            status = await check_beta_status(db=self.db, guild_id=guild.id)
        embed = discord.Embed(title=f"Beta status for {guild.name}", timestamp=datetime.datetime.now())
        if status:
            description = f"Guild ID: {guild.id}\nActive: {status}"
        else:
            description = "Beta? False"
        embed.description = description
        if status:
            embed.color = discord.Color.green()
        else:
            embed.color = discord.Color.red()
        embed.set_footer(text="Dog Knife's The Manager")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)

    @beta_group.command(name="apply", brief="Apply beta to a guild.")
    @commands.is_owner()
    async def apply_beta_to_guild(self, ctx: commands.Context, *, guild: discord.Guild = commands.CurrentGuild):
        async with ctx.typing():
            await self.db.execute("INSERT INTO beta(guildid, active) VALUES($1, True)", guild.id)
        await ctx.reply(f"{guild.name} is now a beta guild!", mention_author=False)

    @beta_group.command(name="remove", brief="Remove beta from a guild.")
    @commands.is_owner()
    async def remove_guild_beta(self, ctx: commands.Context, *, guild: discord.Guild = commands.CurrentGuild):
        async with ctx.typing():
            await self.db.execute("DELETE FROM beta WHERE guildid=$1", guild.id)
        await ctx.reply(f"{guild.name} is no longer a beta guild.", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Beta(bot))
