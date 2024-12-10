from typing import Union

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):
    """Commands to deal with problematic members in your server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @commands.hybrid_command(name="kick", description="Kick a user from your server.", aliases=["kk"])
    @commands.has_permissions(kick_members=True)
    @app_commands.default_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Who you want to kick", reason="The reason for kicking this member.")
    async def kick_command(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        """Kicks a member from your server

        This command respects role hierarchy"""
        await ctx.defer()
        if ctx.me.top_role <= member.top_role:
            return await ctx.send("I cannot moderate this member.", delete_after=5)
        if ctx.author.top_role <= member.top_role and not ctx.guild.owner.id == ctx.author.id:
            return await ctx.send("You cannot moderate this member.", delete_after=5)
        if ctx.guild.owner_id == member.id:
            return await ctx.send("You cannot moderate the server owner.", delete_after=5)
        reason = f"Kicked by {ctx.author.name}. ({reason})"
        await member.kick(reason=reason)
        await ctx.send(f"{member.name} has been kicked.", delete_after=60)

    @commands.hybrid_command(name="ban", description="Ban a user from your server.", aliases=["b"])
    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="Who you want to kick", reason="The reason for kicking this member.")
    async def ban_command(
        self, ctx: commands.Context, user: Union[discord.Member, discord.User], *, reason="No reason provided"
    ):
        """Bans a user from your server.

        This command respects role hierarchy."""
        await ctx.defer()
        reason = f"Banned by {ctx.author.name}. ({reason})"
        if isinstance(user, discord.Member):
            if ctx.me.top_role <= user.top_role:
                return await ctx.send("I cannot moderate this member.", delete_after=5)
            if ctx.author.top_role <= user.top_role and not ctx.guild.owner.id == ctx.author.id:
                return await ctx.send("You cannot moderate this member.", delete_after=5)
            if ctx.guild.owner_id == user.id:
                return await ctx.send("You cannot moderate the server owner.", delete_after=5)
            await user.ban(reason=reason)
        else:
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        await ctx.send(f"{user.name} has been banned", delete_after=60)

    @commands.hybrid_group(
        name="purge", aliases=["p"], description="Purge messages in the current channel.", fallback="messages"
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages you wish to purge.")
    async def purge_group(self, ctx: commands.Context, amount: int):
        await ctx.defer()
        amount = await ctx.channel.purge(limit=amount, reason=f"Purged by {ctx.author.name}")
        await ctx.send(f"{len(amount)} message{'s' if amount != 1 else ''} purged", delete_after=5)

    @purge_group.command(
        name="before",
        aliases=["b"],
        with_app_command=False,
        brief="Purge messages before message. Works with a message or reply",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_before(self, ctx: commands.Context, amount: int, message: discord.Message = None):
        await ctx.defer()
        if message is None:
            if ctx.message.reference:
                message = ctx.message.reference.resolved
            else:
                return await ctx.send("You need to reply to a message, or specify a message.")
        await ctx.message.delete()
        amount = await ctx.channel.purge(limit=amount, before=message)
        await ctx.send(f"{len(amount)} message{'s' if amount != 1 else ''} purged", delete_after=5)

    @purge_group.command(
        name="after",
        aliases=["a"],
        with_app_command=False,
        description="Purge messages after message. Works with a message or reply",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_after(self, ctx: commands.Context, amount: int, message: discord.Message = None):
        await ctx.defer()
        if message is None:
            if ctx.message.reference:
                message = ctx.message.reference.resolved
            else:
                return await ctx.send("You need to reply to a message, or specify a message.")
        amount = await ctx.channel.purge(limit=amount, after=message)
        await ctx.send(f"{len(amount)} message{'s' if amount != 1 else ''} purged", delete_after=5)

    @purge_group.command(name="user", aliases=["member", "users"], description="Purge messages from a user.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages you wish to purge.", user="The user's messages to be purged.")
    async def purge_member(self, ctx: commands.Context, amount: int, user: Union[discord.Member, discord.User]):
        await ctx.defer()
        amount = await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == user.id)
        await ctx.send(f"{len(amount)} message{'s' if amount != 1 else ''} purged", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot), override=True)
