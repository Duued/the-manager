import asyncio
import typing

import discord
from discord import ui
from discord.ext import commands


CHANNELS = [1129457197437419670, 1134688723318091776, 1129458002240479334]


def is_help_forum():
    def check(ctx: commands.Context):
        if not isinstance(ctx.channel, discord.Thread):
            raise commands.CheckFailure("This is not a thread.")
        if ctx.guild and ctx.guild.id == 1120505743913791528:
            if ctx.channel.parent.id in CHANNELS:
                return True
            raise commands.CheckFailure("This is not a valid help forum.")
        else:
            raise commands.CheckFailure("This command must be ran in Dog Knife Development.")

    return commands.check(check)


async def close(thread: discord.Thread, by: typing.Union[discord.Member, discord.User, None] = None):
    if by:
        await thread.edit(locked=True, archived=True, reason=f"Thread was closed by {by.name} ({by.id})")
    else:
        await thread.send("User left guild. Closing...")
        await thread.edit(locked=True, archived=True, reason=f"{thread.owner} ({thread.owner.id}) has left.")


class ConfirmClose(ui.View):
    authorized_user: discord.User
    message: discord.Message | discord.WebhookMessage

    def __init__(self):
        super().__init__(timeout=180)

    @ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.authorized_user:
            await interaction.response.send_message("This confirmation dialog is not for you.", ephemeral=True)
        else:
            await self.message.delete()
            await interaction.response.send_message(
                "Marking as solved. Note that you can mark this as solved next time with `*solved`"
            )
            await asyncio.sleep(10)
            await interaction.channel.edit(locked=True, archived=True)

    @ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.authorized_user:
            await interaction.response.send_message("This confirmation dialog is not for you.", ephemeral=True)
        else:
            await self.message.delete()
            await interaction.response.send_message("Original Poster has cancelled. Not marking as solved.")

    @ui.button(
        label=f'{"Force Close":⠀^25}',
        row=1,
        style=discord.ButtonStyle.danger,
    )
    async def force_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.permissions_for(interaction.user).manage_threads:
            return await interaction.response.send_message("You do not have permission to force close.")
        else:
            await self.message.delete()
            await interaction.response.send_message(
                f"Force closing by {interaction.user.mention} ({interaction.user.id})",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await close(interaction.channel, interaction.user)

    async def on_timeout(self):
        if self.message:
            await self.message.channel.send("Timed out waiting to mark as solved. Not marking as solved.")
            await self.message.delete()


class Forums(commands.Cog):
    """Commands to manage forums"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="solved", description="Mark a thread as solved.")
    @commands.cooldown(1, 300, commands.BucketType.channel)
    @is_help_forum()
    async def thread_is_solved(self, ctx: commands.Context, force: bool = False):
        if force and ctx.channel.permissions_for(ctx.author).manage_threads:
            await ctx.reply(":ok_hand:", mention_author=False)
            await close(ctx.channel, ctx.author)
        elif force:
            raise commands.CheckFailure("You cannot force close threads. Try again with `force` set to `False` or omitted.")
        elif ctx.channel.owner.id == ctx.author.id:
            await ctx.reply(":ok_hand:", mention_author=False)
            await close(ctx.channel, ctx.author)
        elif ctx.channel.owner in ctx.guild.members:
            await ctx.reply("Closing since OP left...", mention_author=False)
            await close(ctx.channel, ctx.author)
        else:
            view = ConfirmClose()
            view.message = await ctx.send(
                f"{ctx.channel.owner.mention}\nWould you like to mark this thread as solved? This request was initiated by {ctx.author.mention}",
                allowed_mentions=discord.AllowedMentions(users=[discord.Object(id=ctx.channel.owner.id)]),
                view=view,
            )
            view.authorized_user = ctx.channel.owner

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != 1120505743913791528:
            return
        forum: discord.ForumChannel
        thread: discord.Thread
        for i in range(len(CHANNELS)):
            forum = member.guild.get_channel(CHANNELS[i])
            for thread in forum.threads:
                if thread and not thread.locked and thread.owner.id == member.id:
                    await close(thread)


async def setup(bot: commands.Bot):
    await bot.add_cog(Forums(bot))
