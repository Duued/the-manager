import datetime
import os
from typing import Optional, Union

import aiohttp
import asyncpg
import discord
import dotenv
import mystbin
from discord import app_commands, ui
from discord.ext import commands

import cache

from . import beta


dotenv.load_dotenv(verbose=True)

tag_cache = cache.Cache(25)


class TagNotFound(Exception):
    def __init__(self, msg="Tag not found."):
        """An error indiciating the tag wasn't found."""
        pass


class CreateTagFromMessageModal(ui.Modal, title="Create tag from message."):
    name = ui.TextInput(
        label="Name", placeholder="Enter the name of this tag", style=discord.TextStyle.short, max_length=100
    )
    content = ui.TextInput(
        label="Content", placeholder="Enter the tag content", style=discord.TextStyle.paragraph, max_length=1500
    )

    def __init__(self, db: asyncpg.pool.Pool, message: discord.Message):
        super().__init__()
        self.db = db
        if message.content:
            self.content.default = discord.utils.escape_markdown(message.clean_content, as_needed=True)

    async def on_submit(self, interaction: discord.Interaction):
        tag = await get_tag(db=self.db, name=self.name.value.lower())
        if tag:
            embed = discord.Embed(
                title="Tag Creation Error",
                description="This tag name has already been taken.\nCopy and paste your content and try a different name.",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(
                f"Tag Content: {discord.utils.escape_markdown(self.content.value)}", embed=embed, ephemeral=True
            )
        await create_tag(db=self.db, name=self.name.value.lower(), content=self.content.value, owner_id=interaction.user.id)
        await interaction.response.send_message(f"Tag {self.name.value} has been created.", ephemeral=True)


class TagReportModal(ui.Modal, title="Global Tag Report Prompt"):
    reason = ui.TextInput(
        label="The reason you are submitting this report",
        placeholder="Type the reason you are reporting this tag.",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=1000,
    )
    message: discord.Message | discord.WebhookMessage
    button: ui.Button
    tag_name: str
    tag_owner: int

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Tag Reported!",
            description=f"Reported by: {interaction.user} ({interaction.user.id})\nTag Name: {self.tag_name}\nTag Owner: {self.tag_owner}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="Reason for report", value=self.reason.value, inline=True)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(os.getenv("report_hook"), session=session)
            await webhook.send(embed=embed)
        self.button.disabled = True
        await self.message.edit(view=self.button.view)
        await interaction.response.send_message("Your report has been submitted", ephemeral=True)


class ReportTagView(ui.View):
    db: asyncpg.pool.Pool
    message: discord.Message
    tag_name: str
    tag_owner: int

    def __init__(self):
        super().__init__(timeout=300)

    @ui.button(label="Report this tag", emoji="\U000026a0", style=discord.ButtonStyle.danger)
    async def report_tag(self, interaction: discord.Interaction, button: ui.Button):
        banned = await self.db.fetchrow("SELECT banned FROM users WHERE id=$1", (interaction.user.id))
        if banned:
            return await interaction.response.send_message("You are banned from using this bot.", ephemeral=True)
        modal = TagReportModal()
        modal.message = self.message
        modal.button = button
        modal.tag_name = self.tag_name
        modal.tag_owner = self.tag_owner
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)


async def get_tag(*, db: asyncpg.pool.Pool, name: str):
    print("Getting tag.")
    print("Attempting to serve from cache")
    results = tag_cache.get(name)
    if not results:
        print("Not found... Serving from DB")
        results = await db.fetchrow("SELECT * FROM globaltag WHERE name=$1", name)
        if results:
            tag_cache.add(name, {"content": results["content"], "locked": results["locked"], "ownerid": results["ownerid"]})
            print("Added DB entry to cache.")
    else:
        print("Served from cache")
    return results


async def create_tag(*, db: asyncpg.pool.Pool, name: str, content: str, owner_id: int, locked=False):
    await db.execute(
        """INSERT INTO globaltag(name, content, ownerid, locked)
                    VALUES($1, $2, $3, $4)
                    """,
        name,
        discord.utils.escape_markdown(content, as_needed=True),
        owner_id,
        locked,
    )


async def edit_tag(*, db: asyncpg.pool.Pool, name: str, content: str):
    await db.execute(
        """UPDATE globaltag
                    SET content=$1
                    WHERE name=$2
                    """,
        discord.utils.escape_markdown(content, as_needed=True),
        name,
    )


async def lock_tag(*, db: asyncpg.pool.Pool, name: str, content: str, locked: bool):
    await db.execute(
        """UPDATE globaltag
                    SET content=$1, ownerid=0, locked=$3
                    WHERE name=$2
                    """,
        content,
        name,
        locked,
    )


async def delete_tag(*, db: asyncpg.pool.Pool, name: str):
    await db.execute(
        """DELETE FROM globaltag
                    WHERE name=$1
                    """,
        name,
    )


async def list_tags(*, db: asyncpg.pool.Pool, user: Union[discord.Member, discord.User, None] = None):
    if user:
        return await db.fetch("SELECT * FROM globaltag WHERE ownerid=$1", user.id)
    else:
        return await db.fetch("SELECT * FROM globaltag")


class GlobalTags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """The global tag command system.

        This is in BETA. Expect bugs."""
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db
        self.mb_client = mystbin.Client(token=os.getenv("MYSTBIN_API_KEY"))

        self.create_tag = app_commands.ContextMenu(name="Create Tag", callback=self.create_from_message)
        self.bot.tree.add_command(self.create_tag)

    async def cog_unload(self):
        self.bot.tree.remove_command(command=self.create_tag.name, type=self.create_tag.type)

    _cooldown = commands.CooldownMapping.from_cooldown(1, 4, commands.BucketType.user)
    _cooldown2 = commands.CooldownMapping.from_cooldown(20, 300, commands.BucketType.guild)
    _ac_cd1 = app_commands.checks.cooldown(1, 4, key=lambda i: i.user.id)
    _max_concurrency = commands.MaxConcurrency(1, per=commands.BucketType.default, wait=True)

    @commands.hybrid_group(fallback="get")
    @app_commands.describe(name="The tag to get.")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def tag(self, ctx: commands.Context, *, name: str):
        """Get a tag.

        If there is no subcommand called, this will attempt to search for a tag."""
        tag = await get_tag(db=self.db, name=name.lower())
        if tag:
            if ctx.message.reference:
                reference = ctx.message.reference
                id = reference.resolved.author.id
            else:
                reference = ctx.message
                id = reference.id
            view = ReportTagView()
            if tag["locked"] is True:
                view = None
            else:
                view.tag_name = name
                view.tag_owner = tag["ownerid"]
                view.db = self.db
            message = await ctx.send(
                tag["content"],
                reference=reference,
                view=view,
                allowed_mentions=discord.AllowedMentions(users=[discord.Object(id)]),
            )
            if not tag["locked"]:
                view.message = message
        else:
            await ctx.send("Tag not found.", reference=ctx.message, mention_author=False)

    @tag.command(aliases=["add"])
    @app_commands.describe(name="The tag name to make", content="The tag content.")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def create(self, ctx: commands.Context, name: str, *, content: str):
        """Create a tag manually."""
        tag = await get_tag(db=self.db, name=name.lower())
        if tag:
            return await ctx.send("This tag already exists.")
        if len(content) > 2000:
            return await ctx.send("Content cannot be greater than 2000 characters.")
        await create_tag(db=self.db, name=name.lower(), content=content, owner_id=ctx.author.id)
        await ctx.send(f"Tag {name} has been created.", reference=ctx.message, mention_author=False)

    @_ac_cd1
    async def create_from_message(self, interaction: discord.Interaction, message: discord.Message):
        """Create a tag from a message"""
        modal = CreateTagFromMessageModal(self.db, message)
        await interaction.response.send_modal(modal)

    @tag.command(aliases=["update"])
    @app_commands.describe(name="The tag name to edit.", content="The new content to replace the old content.")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def edit(self, ctx: commands.Context, name: str, *, content: str):
        """Edit a tag."""
        tag = await get_tag(db=self.db, name=name.lower())
        if tag and tag["ownerid"] == ctx.author.id:
            if len(content) > 2000:
                return await ctx.send("Content cannot be over 2000 characters", reference=ctx.message, mention_author=False)
            await edit_tag(db=self.db, content=content, name=name.lower())
            tag_cache.edit(name.lower(), {"content": content["content"], "locked": False, "ownerid": ctx.author.id})
            msg = "Tag has been edited."
        else:
            msg = "You do not have permission to edit this tag, or it doesn't exist."
        await ctx.send(msg, reference=ctx.message, mention_author=False)

    @tag.command(aliases=["remove"])
    @app_commands.describe(name="The tag name to delete.")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def delete(self, ctx: commands.Context, *, name: str):
        """Delete a tag"""
        tag = await get_tag(db=self.db, name=name.lower())
        if tag and tag["ownerid"] == ctx.author.id:
            await delete_tag(db=self.db, name=name.lower())
            msg = "Tag has been deleted."
        elif tag and await ctx.bot.is_owner(ctx.author):
            await delete_tag(db=self.db, name=name.lower())
            msg = "Tag has been deleted."
        else:
            msg = "You do not have permission to delete this tag, or it doesn't exist."
        await ctx.send(msg, reference=ctx.message, mention_author=False)

    @tag.command(aliases=["owner"])
    @app_commands.describe(name="The tag to get information about")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def info(self, ctx: commands.Context, *, name: str):
        """Get info about a tag"""
        tag = await get_tag(db=self.db, name=name.lower())
        if tag:
            embed = discord.Embed(
                title=f"Tag information for tag `{name}`",
                description=f"Owner: {ctx.bot.get_user(tag['ownerid'])}",
                color=0x00FFA6,
                timestamp=datetime.datetime.now(),
            )
            await ctx.send(embed=embed, reference=ctx.message)
        else:
            await ctx.send("Tag not found.")

    @tag.command(cooldown=_cooldown, max_concurrency=_max_concurrency)
    @app_commands.describe(user="The user's tags to show. Defaults to global if empty")
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    async def list(self, ctx: commands.Context, user: Union[discord.Member, discord.User] = None):
        """List all tags globally or for a user. Defaults to global"""
        text = ""
        rows = await list_tags(db=self.db, user=user)
        if not rows:
            return await ctx.send("No tags found.", reference=ctx.message, mention_author=False)
        for row in rows:
            text += f"Tag Name: {row['name']} - Tag Owner: {row['ownerid']}\n"
        if user:
            filename = f"{user.name}'s tags"
        else:
            filename = "All Tags"
        async with ctx.typing():
            paste = await self.mb_client.create_paste(filename=filename, content=text)
        await ctx.send(paste, reference=ctx.message, mention_author=False)

    @commands.command(cooldown=_cooldown, max_concurency=_max_concurrency)
    @commands.guild_only()
    @app_commands.guild_only()
    @beta.is_beta()
    async def tags(self, ctx: commands.Context, user: Union[discord.Member, discord.User] = None):
        """An alias for tag list"""
        await ctx.invoke(self.list, user=user)

    @commands.command(name="taglock", aliases=["tl", "locktag", "lt"], brief="Locks a tag so it cannot be used or edited.")
    @commands.is_owner()
    async def lock_tag(self, ctx: commands.Context, tag_name: str, *, reason: Optional[str]):
        """'Locks' A tag so it cannot be created or edited."""
        if reason:
            reason = f"This tag was locked for the following reason\n\n**{reason}**"
        else:
            reason = "This tag was locked. No reason was provided."
        if await get_tag(db=self.db, name=tag_name):
            await lock_tag(db=self.db, name=tag_name, content=reason)
        else:
            await create_tag(db=self.db, name=tag_name, content=reason, owner_id=0, locked=True)
        await ctx.send("Tag has been locked.")


async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalTags(bot))
