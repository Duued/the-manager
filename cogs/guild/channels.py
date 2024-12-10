import copy
import typing

import discord
from discord import app_commands, ui
from discord.ext import commands


class Channels(commands.GroupCog, name="channel"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="slowmode", description="Sets the channel's slowmode. You must have manage channel permissions on the target."
    )
    @app_commands.describe(
        hours="The amount of hours for slowmode. Leave this and the others empty to remove.",
        minutes="The amount of minutes for slowmode. Leave this and the others empty to remove.",
        seconds="The amount of seconds for slowmode. Leave this and the others empty to remove.",
    )
    async def channel_slowmode(
        self,
        interaction: discord.Interaction,
        target: typing.Optional[discord.TextChannel],
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ):
        target = target or interaction.channel
        if target.permissions_for(interaction.user).manage_channels:
            time = {"hours": hours * 3600, "minutes": minutes * 60}
            newseconds = time["hours"] + time["minutes"] + seconds
            if newseconds > 21600:  # 6 hours
                return await interaction.response.send_message(
                    "Channel slowmode cannot be greater than 6 hours.", ephemeral=True
                )
            await target.edit(slowmode_delay=newseconds, reason=f"Channel slowmode changed by {interaction.user}")
            await interaction.response.send_message("The channel slowmode has been successfully updated!")
        else:
            await interaction.response.send_message("You do not have permission to edit this channel.")

    @app_commands.command(
        name="topic", description="Sets the channel topic. You must have manage channel permissions on the target."
    )
    @app_commands.describe(topic="The topic to set. Leave empty to remove")
    async def set_channel_topic(
        self, interaction: discord.Interaction, target: typing.Optional[discord.TextChannel], topic: str = None
    ):
        target = target or interaction.channel
        if target.permissions_for(interaction.user).manage_channels:
            await target.edit(topic=topic, reason=f"{interaction.user} has set a new channel topic.")


async def setup(bot):
    await bot.add_cog(Channels(bot))
