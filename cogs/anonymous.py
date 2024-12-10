import random

import discord
from discord import app_commands, utils
from discord.ext import commands


class Anonymous(commands.GroupCog, name="anonymous"):
    def __init__(self, bot):
        self.bot = bot

    async def getanonymouschannel(self, guild: discord.Guild):
        entry = await self.bot.db.execute(
            """
                SELECT channelid FROM anonymous
                WHERE id=$1""",
            (guild.id),
        )
        return entry

    @app_commands.command(name="setup", description="Set up the anonymous chat system.")
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_webhooks=True)
    @app_commands.checks.has_permissions(manage_channels=True, manage_webhooks=True)
    async def setup_anonymous_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        overwrites = {
            interaction.guild.me: discord.PermissionOverwrite(
                manage_messages=True, manage_webhooks=True, manage_channels=True, manage_permissions=True
            ),
            interaction.guild.default_role: discord.PermissionOverwrite(
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False,
                manage_webhooks=False,
            ),
        }
        channel = await interaction.guild.create_text_channel(
            name="anonymous-chatting",
            reason=f"Setting up anonymous chat triggered by {interaction.user}",
            topic="Chat anonymously using the </anonymous message:1124063229048529077> command!",
            overwrites=overwrites,
        )
        await channel.create_webhook(name="managed-by-manager-do-not-edit", reason="Setting up anonymous chatting system.")
        await interaction.edit_original_response(
            content=f"Anonymous chatting channel created.\n**Do not rename the channel**\n{channel.mention}"
        )

    @app_commands.command(name="message", description="Sends an anonymous message in the anonymous chatting channel")
    @app_commands.describe(message="The message to send")
    @app_commands.checks.has_permissions(send_messages=True)
    async def send_anonymous_message(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        channel = utils.find(lambda c: c.name == "anonymous-chatting", interaction.guild.text_channels)
        if channel is None:
            await interaction.edit_original_response(
                content="This server has not set up the anonymous messaging system. Ask someone to set it up."
            )
        else:
            webhook = utils.find(lambda w: w.name == "managed-by-manager-do-not-edit", await channel.webhooks())
            if not webhook:
                await interaction.edit_original_response(
                    content="The webhook was not found. Have someone delete this chanel and run setup again."
                )
            await webhook.send(
                content=message,
                username=f"Anonymous {random.randint(1000, 9999)}",
                avatar_url="https://i.imgur.com/5DYRsqr.png",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await interaction.edit_original_response(content="Sent.")


async def setup(bot):
    await bot.add_cog(Anonymous(bot))
