import datetime
import io
from typing import Union

import aiohttp
import asyncpg
import discord
from discord import ui
from discord.ext import commands, tasks


class CannotApproveRequest(Exception):
    """A custom exception raised when a user cannot approve a global ban request"""

    def __init__(self, msg="You do not have permission to approve this request"):
        self.msg = msg


async def do_bans(records: list[asyncpg.Record], guild: discord.Guild):
    for record in records:
        try:
            await guild.ban(discord.Object(id=record["user_id"]), reason=f"Global Ban for the reason: {record['reason']}")
        except:  # noqa: E722
            continue


def is_dev_server():
    def check(ctx: commands.Context):
        if ctx.guild and ctx.guild.id == 1120505743913791528:
            return True
        raise commands.CheckFailure("This command must be ran in DogKnife Developemnt")

    return commands.check(check)


def has_any_role(member: discord.Member, roles: list[Union[int, discord.Role]]) -> bool:
    for member_role in member.roles:
        for role in roles:
            if isinstance(role, discord.Role):
                if member_role.id == role.id:
                    return True
            else:
                if member_role.id == role:
                    return True
    return False


def can_approve_request():
    async def check(ctx: commands.Context):
        if ctx.guild and ctx.guild.id == 1120505743913791528:
            if has_any_role(ctx.author, [1120513975558352976, 1133201765962109038]):
                return True
            raise commands.CheckFailure("You do not have permission to manage global ban requests")
        raise commands.CheckFailure("This command must be ran in DogKnife Development")

    return commands.check(check)


class GlobalBanModal(ui.Modal, title="Global Ban Information"):
    def __init__(self, db: asyncpg.pool.Pool, against_who: discord.User, proof_attachment: discord.Attachment | str = ""):
        super().__init__()
        self.db = db
        self.against_who = against_who
        if proof_attachment is None or proof_attachment == "":
            proof_attachment = ui.TextInput(label="Proof URL", placeholder="A URL for the proof", default="https://")
            self.add_item(proof_attachment)
        self.proof_attachment: discord.Attachment | str | ui.TextInput = proof_attachment

    reason = ui.TextInput(
        label="Global Ban Reason", placeholder="The reason this user should be global banned", min_length=50, max_length=1024
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        embed = discord.Embed(
            title="Global Ban Report Submitted",
            description=f"{interaction.user.name} ({interaction.user.id}) has filed a global ban request against {self.against_who.name} ({self.against_who.id})",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="Report Reason", value=self.reason.value)
        embed.set_footer(text="Dog Knife's The Manager")
        if isinstance(self.proof_attachment, discord.Attachment):
            if self.proof_attachment.content_type.split("/") == "image":
                fp = io.BytesIO()
                await self.proof_attachment.save(fp)
                embed.set_image(url=fp)
            else:
                await interaction.edit_original_response(content="Expected an image for proof.")
        elif isinstance(self.proof_attachment, str):
            embed.add_field(name="Proof", value=self.proof_attachment)
        else:
            embed.add_field(name="Proof", value=self.proof_attachment.value)

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                "https://discord.com/api/webhooks/1133924988467040287/Ebm4rKvphxlu4lzZK-_jLHhfWJB3Bt8OnDDAxqkKIBpeMvwg0iRg8SjEu9u4BnLGr6Gc",
                session=session,
            )
            await webhook.send(
                content="<@&1143954640753397912>", embed=embed, silent=True, username="The Manager Global Bans"
            )
        await self.db.execute(
            "INSERT INTO global_ban_report(user_id, reported_by, reason) VALUES($1, $2, $3)",
            self.against_who.id,
            interaction.user.id,
            self.reason.value,
        )

        await interaction.edit_original_response(content="Your report has been processed.")


class OpenModalView(ui.View):
    def __init__(self, original_author: discord.User, modal: GlobalBanModal):
        super().__init__()
        self.original_author = original_author
        self.modal = modal

    @ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def continue_prompt(self, interaction: discord.Interaction, button: ui.button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        await interaction.response.send_modal(self.modal)


class GlobalBans(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @tasks.loop()
    async def auto_sync_global_bans(self):
        global_ban_records: asyncpg.Record = await self.db.fetch("SELECT * FROM global_bans")
        config_results: list[asyncpg.Record] = await self.db.fetch("SELECT * FROM guildconfig")
        if config_results:
            for record in config_results:
                if record["auto_sync_global_bans"]:
                    guild = self.bot.get_guild(record["guild_id"])
                    if guild:
                        await do_bans(global_ban_records, guild)

    @commands.group(name="globalban", aliases=["gb", "gban"], invoke_without_command=True)
    async def globalban_group(
        self, ctx: commands.Context, user: discord.User, proof_attachment: discord.Attachment | str = ""
    ):
        """Request a user to be global banned."""
        if ctx.author.id == user.id:
            raise commands.CheckFailure("You cannot global ban yourself.")
        elif await ctx.bot.is_owner(user):
            raise commands.CheckFailure("This account is immune to global bans.")
        if ctx.channel.permissions_for(ctx.me).manage_channels:
            await ctx.message.delete()
        modal = GlobalBanModal(self.db, user, proof_attachment)
        view = OpenModalView(ctx.author, modal)
        await ctx.send("Please click this button to continue!", view=view)

    @globalban_group.command(name="approve", aliases=["accept"])
    @can_approve_request()
    async def gban_approve(self, ctx: commands.Context, reported_user: discord.User):
        """Approve a global ban request."""
        record: asyncpg.Record | None = await self.db.fetchrow(
            "SELECT * FROM global_ban_report WHERE user_id=$1", reported_user.id
        )
        if record:
            if record["reported_by"] == ctx.author.id:
                raise CannotApproveRequest("You cannot approve your own global ban request.")
            await self.db.execute("DELETE FROM global_ban_report WHERE user_id=$1", reported_user.id)
            await self.db.execute(
                "INSERT INTO global_bans(user_id, reported_by, approved_by, reason) VALUES($1, $2, $3, $4)",
                reported_user.id,
                record["reported_by"],
                ctx.author.id,
                record["reason"],
            )
            embed = discord.Embed(
                title="Global Ban Accepted", color=discord.Color.green(), timestamp=datetime.datetime.now()
            )
            embed.description = f"Report submitted by `{record['reported_by']}` against `{record['user_id']}` accepted by {ctx.author.mention}"
            embed.set_footer(text="Dog Knife's The Manager")
            embed.add_field(name="Report Reason", value=record["reason"])
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    "https://discord.com/api/webhooks/1133924988467040287/Ebm4rKvphxlu4lzZK-_jLHhfWJB3Bt8OnDDAxqkKIBpeMvwg0iRg8SjEu9u4BnLGr6Gc",
                    session=session,
                )
                await webhook.send(embed=embed, username="The Manager Global Bans", silent=True)
            await ctx.send("Global Ban Approved.")
            if self.auto_sync_global_bans.is_running():
                self.auto_sync_global_bans.restart()
            else:
                self.auto_sync_global_bans.start()
        else:
            await ctx.send("Report not found. Make sure to use the **user ID**")

    @globalban_group.command(name="deny", aliases=["reject"])
    @can_approve_request()
    async def gban_deny(self, ctx: commands.Context, reported_user: discord.User):
        """Deny a global ban request."""
        record: asyncpg.Record | None = await self.db.fetchrow(
            "SELECT * FROM global_ban_report WHERE user_id=$1", reported_user.id
        )
        if record:
            if record["reported_by"] == ctx.author.id:
                raise CannotApproveRequest("You cannot deny your own global ban request.")
            await self.db.execute("DELETE FROM global_ban_report WHERE user_id=$1", reported_user.id)
            embed = discord.Embed(title="Global Ban Rejected", color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.description = f"Report submitted by `{record['reported_by']}` against `{record['user_id']}` rejected by {ctx.author.mention}"
            embed.set_footer(text="Dog Knife's The Manager")
            embed.add_field(name="Report Reason", value=record["reason"])
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    "https://discord.com/api/webhooks/1133924988467040287/Ebm4rKvphxlu4lzZK-_jLHhfWJB3Bt8OnDDAxqkKIBpeMvwg0iRg8SjEu9u4BnLGr6Gc",
                    session=session,
                )
                await webhook.send(embed=embed, username="The Manager Global Bans", silent=True)
            await ctx.send("Global Ban Rejected.")
        else:
            await ctx.send("Report not found. Make sure to use the **user ID**")

    @globalban_group.command(name="override")
    @commands.is_owner()
    async def gban_override(self, ctx: commands.Context, offending_user: discord.User, *, reason: str):
        """Global ban someone immediately"""
        record: asyncpg.Record | None = await self.db.fetchrow(
            "SELECT * FROM global_ban_report WHERE user_id=$1", offending_user.id
        )
        if record:
            await self.db.execute("DELETE FROM global_ban_report WHERE user_id=$1", offending_user.id)
        await self.db.execute(
            "INSERT INTO global_bans(user_id, reported_by, reason, approved_by) VALUES($1, $2, $3, $4)",
            offending_user.id,
            0,
            reason,
            ctx.author.id,
        )
        embed = discord.Embed(title="Global Ban Overridden", color=discord.Color.red(), timestamp=datetime.datetime.now())
        embed.description = f"`{offending_user.id}` has been force-banned by {ctx.author.mention}"
        embed.set_footer(text="Dog Knife's The Manager")
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                "https://discord.com/api/webhooks/1133924988467040287/Ebm4rKvphxlu4lzZK-_jLHhfWJB3Bt8OnDDAxqkKIBpeMvwg0iRg8SjEu9u4BnLGr6Gc",
                session=session,
            )
            await webhook.send(embed=embed, username="The Manager Global Bans", silent=True)
        await ctx.send("Global Ban Overridden.")
        if self.auto_sync_global_bans.is_running():
            self.auto_sync_global_bans.restart()
        else:
            self.auto_sync_global_bans.start()

    @globalban_group.command(name="sync")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True, ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def gban_sync_guild(self, ctx: commands.Context):
        enabled: asyncpg.Record = await self.db.fetchval("SELECT * FROM guildconfig WHERE guild_id=$1", ctx.guild.id)
        if enabled:
            message = await ctx.send("Syncing bans...")
            records: asyncpg.Record = await self.db.fetch("SELECT * FROM global_bans")
            await do_bans(records, ctx.guild)
            await message.edit(content="Bans have been synced.")
        else:
            await ctx.send("Please edit your guild configuration to enable global bans.")

    @globalban_group.command(name="check")
    @is_dev_server()
    async def gban_check_if_banned(self, ctx: commands.Context, user: discord.User):
        banned: asyncpg.Record = await self.db.fetch("SELECT * FROM global_bans WHERE user_id=$1", user.id)
        if banned:
            msg = f"{user.mention} is currently global banned."
        else:
            msg = f"{user.mention} is not global banned."
        await ctx.send(msg, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalBans(bot))
