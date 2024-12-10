import datetime

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


class GuildConfigEmbed(discord.Embed):
    def __init__(self, db: asyncpg.pool.Pool, guild: discord.Guild):
        super().__init__()
        self.db = db
        self.guild = guild
        self.timestamp = datetime.datetime.now()
        self.set_footer(text="Dog Knife's The Manager")
        self.color = 0x7289DA

    async def setup(self):
        config = await self.db.fetchrow("SELECT * FROM guildconfig WHERE guild_id=$1", self.guild.id)
        if not config or config == []:
            await self.db.execute("INSERT INTO guildconfig (guild_id) VALUES($1)", self.guild.id)
            config = await self.db.fetchrow("SELECT * FROM guildconfig WHERE guild_id=$1", self.guild.id)
        self.description = "True = On, False = Off"
        self.add_field(name="Use Global Ban System", value=config["global_bans_enabled"])
        self.add_field(name="Auto Sync Global Bans", value=config["auto_sync_global_bans"])


class ConfigEmbed(discord.Embed):
    def __init__(self, db: asyncpg.pool.Pool, user: discord.User):
        super().__init__()
        self.db = db
        self.user = user
        self.color = 0x7289DA
        self.timestamp = datetime.datetime.now()
        self.set_footer(text="Dog Knife's The Manager")

    async def setup(self):
        config = await self.db.fetchrow("SELECT * FROM userconfig WHERE user_id=$1;", self.user.id)
        if not config or config == []:
            await self.db.execute("INSERT INTO userconfig (user_id) VALUES($1);", self.user.id)
            config = await self.db.fetchrow("SELECT * FROM userconfig WHERE user_id=$1;", self.user.id)
        self.description = "True = On, False = Off"
        self.add_field(name="Economy Work Notifications", value=config["work_notifications"])
        self.add_field(name="Economy Crime Notifications", value=config["crime_notifications"])
        self.add_field(name="Economy Rob Notifications", value=config["rob_notifications"])


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    config_group = app_commands.Group(name="config", description="Bot configuration commands for yourself or the guild.")

    @config_group.command(name="user", description="Set up your own user configuration")
    @app_commands.choices(
        update_key=[
            app_commands.Choice(name="Work Notifications", value="work_notifications"),
            app_commands.Choice(name="Crime Notifications", value="crime_notifications"),
            app_commands.Choice(name="Rob Notifications", value="rob_notifications"),
            app_commands.Choice(name="All Notifications", value="all_notifications"),
        ]
    )
    @app_commands.describe(update_key="The user configuration key to update", value="The new value of your update key.")
    async def user_config(self, interaction: discord.Interaction, update_key: str = None, value: bool = None):
        if update_key is not None:
            if value is None or value == "":
                return await interaction.response.send_message(
                    "To edit a configuration key, you must provide a value", ephemeral=True
                )
            else:
                if update_key == "all_notifications":
                    notifications = ["work_notifications", "crime_notifications", "rob_notifications"]
                    for update_key in notifications:
                        await self.db.execute(
                            f"INSERT INTO userconfig(user_id, {update_key}) VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET {update_key}=$2",
                            interaction.user.id,
                            value,
                        )
                else:
                    await self.db.execute(
                        f"INSERT INTO userconfig(user_id, {update_key}) VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET {update_key}=$2",
                        interaction.user.id,
                        value,
                    )
        embed = ConfigEmbed(self.db, interaction.user)
        await embed.setup()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="guildconfig", description="Configure your guild settings.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.choices(
        update_key=[
            app_commands.Choice(name="Global Bans", value="global_bans_enabled"),
            app_commands.Choice(name="Auto Sync Global Bans", value="auto_sync_global_bans"),
        ]
    )
    @app_commands.describe(update_key="The guild configuration key to update", value="The new value of your key.")
    async def guild_config(self, interaction: discord.Interaction, update_key: str = None, value: bool = None):
        if update_key is not None:
            if value is None or value == "":
                return await interaction.response.send_message(
                    "To edit a configuration key, you must provide a value.", ephemeral=True
                )
            else:
                if update_key == "global_bans_enabled":
                    await self.db.execute(
                        f"INSERT INTO guildconfig (guild_id, {update_key}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {update_key}=$2",
                        interaction.guild.id,
                        value,
                    )
                elif update_key == "auto_sync_global_bans":
                    await self.db.execute(
                        f"INSERT INTO guildconfig (guild_id, {update_key}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {update_key}=$2",
                        interaction.guild.id,
                        value,
                    )

        embed = GuildConfigEmbed(self.db, interaction.guild)
        await embed.setup()
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
