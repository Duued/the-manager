import datetime
import typing

import discord
from discord import app_commands
from discord.ext import commands


def guild_check():
    def predicate(interaction: discord.Interaction):
        if interaction.guild:
            return True
        raise app_commands.CheckFailure("This command must be ran in a guild")

    return app_commands.check(predicate)


class InfoEmbed(discord.Embed):
    def add_fields(self):
        object = self.object
        member_info = self.member_info
        fields = [
            {
                "name": "Members",
                "value": f"""- Users: {member_info['Users']}
- Bots: {member_info['Bots']}
- Total: {member_info['Total']}""",
            },
            {
                "name": "Statistics",
                "value": f"""
- Percent of Users: {len([m for m in object.members if not m.bot])/len(object.members)* 100:.2f}%
- Percent of Bots: {len([m for m in object.members if m.bot])/len(object.members)* 100:.2f}%
""",  # await ctx.send(f"{len([member for member in guild.members if member.bot])/len(guild.members):.2f}%")
            },
            {"name": "Roles", "value": f"- Total: {len(object.roles)}"},
            {
                "name": "Channels",
                "value": f"""- All: {len(object.channels)}
- Text: {len(object.text_channels)}
- Voice: {len(object.voice_channels)}
- Stage: {len(object.stage_channels)}
- Forums: {len(object.forums)}""",
            },
        ]
        for field in fields:
            self.add_field(name=field["name"], value=field["value"], inline=True)

    def __init__(
        self,
        author: typing.Union[discord.Member, discord.User],
        object: typing.Union[discord.Member, discord.User, discord.TextChannel, discord.Guild],
    ):
        super().__init__()
        self.title = f"<:info:1131686417110675537> Information for {object.name} <:info:1131686417110675537>"
        self.color = discord.Color.random()
        self.timestamp = datetime.datetime.now()
        self.object = object

        self.set_author(name=author.name, icon_url=author.guild_avatar or author.display_avatar)
        self.set_footer(text="Dog Knife's The Manager")
        created_at = object.created_at
        if isinstance(object, discord.Member):
            joined_at = object.joined_at
            self.description = f"""
            User Name: {object.name}#{object.discriminator}

            User ID: {object.id}

            Created At: {discord.utils.format_dt(created_at, "f")} ({discord.utils.format_dt(created_at, "R")})

            Joined At: {discord.utils.format_dt(joined_at, "f")} ({discord.utils.format_dt(joined_at, "R")})
            """
            image = object.guild_avatar or object.display_avatar
            self.set_thumbnail(url=image)
        elif isinstance(object, discord.User):
            self.description = f"""
            User Name: {object.name}#{object.discriminator}

            User ID: {object.id}

            Created At: {discord.utils.format_dt(created_at, "f")} ({discord.utils.format_dt(created_at, "R")})
            """
            self.set_thumbnail(url=object.display_avatar)
        elif isinstance(object, discord.TextChannel):
            self.description = f"""
            Channel Name: {object.name}

            Channel ID: {object.id}

            NSFW? {object.nsfw}

            Created At: {discord.utils.format_dt(created_at, "f")} ({discord.utils.format_dt(created_at, "R")})

            Parent Category: {object.category.mention}
            """
        elif isinstance(object, discord.Guild):
            member_info: dict = {
                "Users": len([m for m in object.members if not m.bot]),
                "Bots": len([m for m in object.members if m.bot]),
                "Total": len(object.members),
            }
            self.member_info = member_info
            self.description = f"""
**Guild Name**: {object.name}

**Guild ID**: {object.id}

**Guild Owner**: {object.owner.mention} ({object.owner.id})

**Guild Created At**: {discord.utils.format_dt(created_at, "f")} ({discord.utils.format_dt(created_at, "R")})




            """
            self.set_thumbnail(url=object.icon.url)

            self.add_fields()


class Info(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="user", description="Get information about a user.")
    @app_commands.describe(user="The user to see information about. Leave blank for current.")
    async def get_user_information(
        self, interaction: discord.Interaction, user: typing.Union[discord.Member, discord.User] = None
    ):
        embed = InfoEmbed(interaction.user, user or interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channel", description="Get information about a channel.")
    @app_commands.describe(channel="The channel to get information about. Leave blank for current.")
    async def get_channel_information(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        embed = InfoEmbed(interaction.user, channel or interaction.channel)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="guild",
        description="Get information about the server. Shows as much information as possible, determined by permissions.",
    )
    @guild_check()
    async def get_guild_info(self, interaction: discord.Interaction):
        embed = InfoEmbed(interaction.user, interaction.guild)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
