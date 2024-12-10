import asyncio
import copy
import typing
from typing import Optional, Union

import asyncpg
import discord
from discord.ext import commands

from cogs.info import InfoEmbed


# class DevSlashCommands(commands.GroupCog, name="dev"):
#    def __init__(self, bot):
#        self.bot = bot
#
#
#    async def interaction_check(self, interaction: discord.Interaction):
#        if await self.bot.is_owner(interaction.user):
#            return True


class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    async def cog_check(self, ctx: commands.Context):
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.CheckFailure(f"You must own this bot to use {ctx.command.qualified_name}")

    @commands.command(name="runas", brief="Run as another user, optionally in another channel")
    async def runas(
        self,
        ctx: commands.Context,
        user: typing.Union[discord.Member, discord.User],
        channel: typing.Optional[discord.TextChannel],
        command: str,
    ):
        newmsg = copy.copy(ctx.message)
        new_channel = channel or ctx.channel
        newmsg.channel = new_channel
        newmsg.author = user
        newmsg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(newmsg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command(name="sudo", aliases=["force", "run", "forcerun"])
    async def run_sudo(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        user: Optional[Union[discord.Member, discord.User]],
        *,
        command_string: str,
    ):
        """Run a command bypassing all checks and cooldowns.

        Can optionally run as other user or in another channel."""
        if not ctx.prefix:
            raise commands.CommandInvokeError("Must be invoked with prefix.")
        newmsg = copy.copy(ctx.message)
        new_chanel = channel or ctx.channel
        newmsg.author = user or ctx.author
        newmsg.channel = new_chanel
        newmsg.content = ctx.prefix + command_string
        new_ctx: commands.Context = await self.bot.get_context(newmsg, cls=type(ctx))
        await new_ctx.reinvoke()

    @commands.group(name="lockstatus", aliases=["ls"], invoke_without_command=True, brief="Get the current bot lock status.")
    async def lock(self, ctx: commands.Context):
        embed = discord.Embed(title=f"Bot Locked?: {self.bot.locked}", color=0x7289DA)
        await ctx.send(embed=embed)

    @lock.command(name="lock", aliases=["l"], brief="Set the current bot lock status to locked.")
    async def lock_bot(self, ctx: commands.Context):
        self.bot.locked = True
        await ctx.send("The bot is now locked.")

    @lock.command(name="unlock", aliases=["ul"], brief="Set the current bot lock status to unlocked.")
    async def unlock_bot(self, ctx: commands.Context):
        self.bot.locked = False
        await ctx.send("The bot is now unlocked.")

    @commands.command(name="userban", aliases=["uban"], brief="Ban a user from using the bot.")
    async def user_ban(self, ctx: commands.Context, user: discord.User):
        data = await self.db.fetch("SELECT banned FROM users WHERE id=$1", (user.id))
        if not data:
            await self.db.execute(
                """INSERT INTO users (id, banned)
                VALUES($1, True)""",
                (user.id),
            )
            await ctx.reply("User has been banned.", mention_author=False)
        else:
            raise commands.CommandInvokeError("User is already banned.")

    @commands.command(name="userunban", aliases=["unuban"], brief="Ban a user from using the bot.")
    async def user_unban(self, ctx: commands.Context, user: discord.User):
        data = self.db.fetch("SELECT banned FROM users WHERE id=$1", (user.id))
        if data:
            await self.db.execute(
                """DELETE FROM users
                
                WHERE id=$1                
                """,
                (user.id),
            )
            await ctx.reply("User has been unbanned.", mention_author=False)
        else:
            raise commands.CommandInvokeError("User was not banned.")

    @commands.command(name="guild", aliases=["gi", "ginfo", "guildinfo"], brief="Get a specific guild, or current guild.")
    async def get_guild_info(self, ctx: commands.Context, *, guild: discord.Guild = None):
        """Get guild info. Owner only, use slash command as the public version"""
        guild: discord.Guild = guild or ctx.guild or None
        if guild:
            embed = InfoEmbed(ctx.author, guild)
            await ctx.send(embed=embed)
        else:
            raise commands.CommandInvokeError("Guild was none, cannot default to current guild as we are in a DM.")

    @commands.command(name="quit", aliases=["logout", "shutdown", "fuckoff"])
    async def quit(self, ctx: commands.Context):
        await ctx.reply(":ok_hand:", mention_author=False)
        await ctx.bot.close()

    @commands.group(name="send", brief="Sends messages to a channel", invoke_without_command=True)
    async def send_message(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        await channel.send(message)
        await ctx.send("Sent", delete_after=5)

    @send_message.command(name="type", aliases=["typing"], brief="Simulate typing while sending message")
    async def send_typing_message(self, ctx: commands.Context, channel: discord.TextChannel, time: float, *, message: str):
        async with channel.typing():
            await asyncio.sleep(time)
        await channel.send(message)
        await ctx.send("Sent", delete_after=5)


async def setup(bot):
    # await bot.add_cog(DevSlashCommands(bot))
    await bot.add_cog(DevCommands(bot))
