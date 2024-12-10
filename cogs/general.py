import datetime
import sys
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands


class DiagnosisEmbed(discord.Embed):
    """A class to generate and modify the diagnosis embed"""

    def __init__(self, *, channel: discord.TextChannel):
        super().__init__()

        self.channel = channel
        self.title = f"Diagnosis for {channel.name}"
        self.set_footer(
            text="Command written by @dogknife", icon_url="https://fretgfr.com/u/680fa6cd-9492-47a9-94d6-90d62cc16fa9.png"
        )
        self.color = 0x7289DA
        self.do_diagnosis()

    def do_diagnosis(self):
        me = self.channel.guild.me

        if me.guild_permissions.administrator:
            to_send = "Administrator granted. All permissions are granted."
            self.description = to_send
            return
        permissions = self.channel.permissions_for(me)
        permtext = {}
        if permissions.read_messages:
            permtext["view_channel"] = (True, "This permission is granted. Necessary to function properly.")
        else:
            permtext["view_channel"] = (False, "This permission is denied. Necessary to function properly.")

        if permissions.embed_links:
            permtext["embed_links"] = (True, "This permission is granted. Necessary to send embeds.")
        else:
            permtext["embed_links"] = (False, "This permission is denied. Necessary to send embeds.")

        if permissions.attach_files:
            permtext["attach_files"] = (True, "This permission is granted. Necessary to send files.")
        else:
            permtext["attach_files"] = (False, "This permission is denied. Necessary to send files.")

        to_send = ""
        for key, value in permtext.items():
            if value[0]:
                to_send += f":white_check_mark: Permission: `{key}`. {value[1]}\n"
            else:
                to_send += f":x: Permission: `{key}`. {value[1]}\n"
        self.description = to_send


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.support_guild_id = 1120505743913791528
        self.staff_roles: list[dict] = [
            {"role_id": 1120507728977203310, "display_name": "Developer"},
            {"role_id": 1120513975558352976, "display_name": "Support Server Administrator"},
            {"role_id": 1131769457497354281, "display_name": "Official Support Member"},
        ]

    @commands.hybrid_command(name="bot", aliases=["info"], description="Gives you various different bot information.")
    async def give_bot_information(self, ctx: commands.Context):
        guild: discord.Guild = ctx.bot.get_guild(1120505743913791528)
        bot_invite_embed = discord.Embed(
            type="link",
            title="Bot Invite",
            description="The bot's invite URL.",
            url=ctx.bot.application.custom_install_url,
        )
        bot_invite_embed.set_thumbnail(url=ctx.bot.user.display_avatar)

        support_server = discord.Embed(
            type="link",
            title="Support Server",
            description="The support server for the bot, or to learn different programming languages.",
            url="https://discord.gg/2yjqaAmjyq",
        )
        support_server.set_thumbnail(url=guild.icon.url if guild.icon else None)

        documentation = discord.Embed(
            type="link",
            title="Bot Documentation",
            description="The bot's official documentation.",
            url="https://the-manager.gitbook.io/the-manager",
        )
        documentation.set_thumbnail(url=ctx.bot.user.display_avatar)

        embeds = [bot_invite_embed, support_server, documentation]
        for embed in embeds:
            embed.color = 0x7289DA
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text="Dog Knife's The Manager")
        await ctx.send(embeds=embeds)

    @commands.hybrid_command(name="support", description="Gives you my support server invite.")
    async def support_server_invite(self, ctx: commands.Context):
        guild: discord.Guild = ctx.bot.get_guild(1120505743913791528)
        support_server = discord.Embed(
            type="link",
            title="Support Server",
            description="The support server for the bot, or to learn different programming languages.",
            url="https://discord.gg/2yjqaAmjyq",
        )
        support_server.set_thumbnail(url=guild.icon.url if guild.icon else None)

    @commands.hybrid_command(name="stats")
    async def _bot_stats(self, ctx: commands.Context):
        """Gets different statistics on the bot"""
        embed = discord.Embed(title="The Manager Stats", color=0x7289DA, timestamp=datetime.datetime.now())
        embed.add_field(name="Owner", value="dogknife (<@561565119201673216>)", inline=False)
        embed.add_field(
            name="Python Version <:python:1133106028465106986>", value=f'`{sys.version.split(" ")[0]}`', inline=False
        )
        embed.add_field(
            name="Discord.py Version <:discordpy:1141950056526774304>", value=f"`{discord.__version__}`", inline=False
        )
        embed.add_field(name="Guilds", value=len(ctx.bot.guilds), inline=False)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="application", aliases=["app", "appinfo"])
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def _bot_app_info(self, ctx: commands.Context):
        """Get different application information about the bot."""
        embed = discord.Embed(title="The Manager Application Information", color=0x7289DA)
        app_info: discord.AppInfo = ctx.bot.application
        embed.add_field(name="Application Name", value=app_info.name, inline=False)
        embed.add_field(name="Application ID", value=app_info.id, inline=False)
        embed.add_field(name="Application Description", value=app_info.description, inline=False)
        embed.add_field(name="Application Owner", value=f"{app_info.owner.name}\n{app_info.owner.mention}")
        embed.add_field(name="Public Bot?", value=app_info.bot_public)
        embed.add_field(name="Installation URL", value=f"[Invite The Manager]({app_info.custom_install_url})")
        embed.add_field(name="Servers", value=len(ctx.bot.guilds), inline=True)
        tags = app_info.tags
        tag_text = ""
        for tag in tags:
            tag_text += f"{tag}, "
        tag_text = tag_text.rstrip(", ")
        embed.add_field(name="Bot Tags", value=tag_text, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="checkstaff", aliases=["staffcheck", "isstaff"], hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def check_user_staff_position(self, ctx: commands.Context, user: discord.User):
        guild: discord.Guild | None = ctx.bot.get_guild(self.support_guild_id)
        if not guild:
            raise commands.CommandInvokeError("Support Guild was not found.")
        member: discord.Member = guild.get_member(user.id)
        is_staff = False
        name = ""

        embed = discord.Embed(
            title="This user is not a verified support staff member.",
            description="This user is not a support staff member.\nBe aware, this user may attempt to give you misleading, malicious or incorrect advice.",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        if member:
            for staff_role in self.staff_roles:
                if member.get_role(staff_role["role_id"]):
                    is_staff = True
                    name = staff_role["display_name"]
                    break

            if is_staff:
                embed.title = "User is a verified support staff member."
                embed.description = f"This user is a verified staff member.\nRank name: {name}"
                embed.color = discord.Color.green()
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="diagnose", description="Detect potential issues.")
    @commands.cooldown(2, 10, commands.BucketType.user)
    @app_commands.describe(channel="The target channel to check permissions for.")
    async def diagnose_potential_issues(self, ctx: commands.Context, channel: discord.TextChannel = commands.CurrentChannel):
        embed = DiagnosisEmbed(channel=channel)
        await ctx.send(embed=embed)

    @commands.command(name="betterdiagnose", aliases=["forcediagnose", "diagnose2", "diagnosev2"])
    @commands.is_owner()
    async def diagnose_potential_issues_v2(
        self, ctx: commands.Context, channel: Union[discord.TextChannel, int] = commands.CurrentChannel
    ):
        if isinstance(channel, int):
            channel = ctx.bot.get_channel(channel)
        embed = DiagnosisEmbed(channel=channel)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
