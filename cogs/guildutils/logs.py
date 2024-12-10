import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

from cogs import beta


class Database(asyncpg.Pool):
    def __init__(self, db: asyncpg.Pool):
        self.db = db

    async def get_log_config(self, guild_id: int) -> asyncpg.Record | None:
        return await self.fetchrow("SELECT * FROM guild_log_config WHERE guild_id=$1", guild_id)

    async def get_message_log_config(self, guild_id: int) -> asyncpg.Record | None:
        return await self.fetchval("SELECT message_log_id FROM guild_log_config WHERE guild_id=$1", guild_id)

    async def get_member_traffic_log_config(self, guild_id: int) -> asyncpg.Record | None:
        return await self.fetchval("SELECT member_traffic_log_id FROM guild_log_config WHERE guild_id=$1", guild_id)

    async def get_mod_action_log_config(self, guild_id: int) -> asyncpg.Record | None:
        return await self.fetchval("SELECT mod_event_log_id FROM guild_log_config WHERE guild_id=$1", guild_id)

    async def set_message_log_config(self, guild_id: int, channel: discord.TextChannel) -> None:
        await self.execute(
            """INSERT INTO guild_log_config (guild_id, message_log_id)
                            ON CONFLICT(guild_id) DO UPDATE SET message_log_id=$2""",
            guild_id,
            channel.id,
        )

    async def set_member_traffic_log_config(self, guild_id: int, channel: discord.TextChannel) -> None:
        await self.execute(
            """INSERT INTO guild_log_config (guild_id, member_traffic_log_id)
                            ON CONFLICT(guild_id) DO UPDATE SET member_traffic_log_id=$2""",
            guild_id,
            channel.id,
        )

    async def set_mod_action_log_config(self, guild_id: int, channel: discord.TextChannel) -> None:
        await self.execute(
            """INSERT INTO guild_log_config (guild_id, mod_event_log_id)
                            ON CONFLICT(guild_id) DO UPDATE SET mod_event_log_id=$2""",
            guild_id,
            channel.id,
        )


class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool
        self.log_database = Database(self.db)

    # @commands.Cog.listener()
    # async def on_message_edit(self, message: discord.Message):

    @app_commands.command(name="logs", description="Configure logs.")
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Message Logs", value="message_logs"),
            app_commands.Choice(name="Mod Logs", value="mod_logs"),
            app_commands.Choice(name="Traffic Logs", value="traffic_logs"),
        ]
    )
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild.id)
    async def configure_message_log(self, interaction: discord.Interaction, type: str, target_channel: discord.TextChannel):
        if target_channel.permissions_for(interaction.guild.me).manage_webhooks == False:
            return await interaction.response.send_message(
                "I am missing `manage_webhooks` in the target channel.", ephemeral=True
            )
        webhook = await target_channel.create_webhook(
            name="The Manager Logging", avatar=interaction.client.user.display_avatar
        )
        if type == "message_logs":
            await self.log_database.set_message_log_config(interaction.guild.id, webhook)
            msg = f"Message logs successfully set to {target_channel.mention}"
        elif type == "mod_logs":
            await self.log_database.set_mod_action_log_config(interaction.guild.id, webhook)
            msg = f"Moderation action logs successfully set to {target_channel.mention}"
        elif type == "traffic_logs":
            await self.log_database.set_member_traffic_log_config(interaction.guild.id, webhook)
            msg = f"Member join/leave log successfully set to {target_channel.mention}"
        await interaction.response.send_message(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
