import datetime
from typing import Optional, Union

import asyncpg
import discord
from discord import ui
from discord.ext import commands

from cogs import beta


class AddAutoRoleSelect(ui.View):
    db: asyncpg.pool.Pool
    original_author: Union[discord.User, discord.Member]
    message: discord.Message | discord.WebhookMessage

    @ui.select(
        cls=ui.RoleSelect, placeholder="The role(s) to automatically assign to joining members.", min_values=1, max_values=25
    )
    async def add_selected_roles(self, interaction: discord.Interaction, select: ui.RoleSelect):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This menu is not for you.", ephemeral=True)
        text = ""
        for role in select.values:
            if role.is_default():
                text += "Cannot add the @everyone role to auto roles.\n"
            elif role.is_bot_managed():
                text += f"{role.mention} Cannot be added as it is a bot-managed role.\n"
            elif role.position >= interaction.guild.me.top_role.position:
                text += f"{role.mention} is higher than my role. Cannot be added."
            elif role.position >= interaction.user.top_role.position:
                text += f"{role.mention} is higher than your top role. Cannot be added."
            else:
                results = await fetch(self.db, role=role)
                if results:
                    text += f"{role.mention} is already an auto role!\n"
                else:
                    await self.db.execute(
                        "INSERT INTO autoroles(guildid, role) VALUES($1, $2)", interaction.guild.id, role.id
                    )
                    text += f"{role.mention} was successfully added to the auto roles!\n"
        embed = discord.Embed(
            title="Auto Role Add Result",
            description=text,
            color=discord.Color.og_blurple(),
            timestamp=datetime.datetime.now(),
        )
        await interaction.response.send_message(embed=embed)
        await self.message.edit(view=None)


class RemoveAutoRoleSelect(ui.View):
    db: asyncpg.pool.Pool
    original_author: Union[discord.User, discord.Member]
    message: discord.Message | discord.WebhookMessage

    @ui.select(
        cls=ui.RoleSelect,
        placeholder="Roles to remove that are currently being assigned to joining members.",
        min_values=1,
        max_values=25,
    )
    async def remove_selected_roles(self, interaction: discord.Interaction, select: ui.RoleSelect):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This menu is not for you.", ephemeral=True)
        text = ""
        for role in select.values:
            if role.is_default():
                text += "Cannot remove the @everyone role from auto roles."
            elif role.is_bot_managed():
                text += f"{role.mention} Cannot be removed as it is a bot-managed role.\n"
            elif role.position >= interaction.guild.me.top_role.position:
                text += f"{role.mention} is higher than my role. Cannot be removed."
            elif role.position >= interaction.user.top_role.position:
                text += f"{role.mention} is higher than your top role. Cannot be removed."
            else:
                results = await fetch(self.db, role=role)
                if results:
                    await self.db.execute("DELETE FROM autoroles WHERE role=$1", role.id)
                else:
                    text += f"{role.mention} is not currently an auto role."
        embed = discord.Embed(
            title="Auto Role Remove Result",
            description=text,
            color=discord.Color.og_blurple(),
            timestamp=datetime.datetime.now(),
        )
        await interaction.response.send_message(embed=embed)
        await self.message.edit(view=None)


async def fetch(db: asyncpg.pool.Pool, *, role: discord.Role) -> asyncpg.Record | None:
    return await db.fetch("SELECT * FROM autoroles WHERE role=$1", role.id)


async def get(db: asyncpg.pool.Pool, *, guild_id: Optional[int] = None, role: Optional[discord.Role] = None) -> str:
    if guild_id:
        query = "SELECT * FROM autoroles WHERE guildid=$1"
        obj = guild_id
    else:
        query = "SELECT * FROM autoroles WHERE role=$1"
        obj = role.id
    rows = await db.fetchrow(query, obj)

    text = ""
    if rows:
        for role in rows:
            text += f"{role.mention}\n"
    else:
        text = "No auto roles."
    return text


async def get_embed(db: asyncpg.pool.Pool, *, guild: discord.Guild) -> discord.Embed:
    query = "SELECT * FROM autoroles WHERE guildid=$1"
    rows = await db.fetch(query, guild.id)

    text = ""
    if rows:
        color = discord.Color.green()
        for row in rows:
            text += f"{guild.get_role(row['role']).mention}\n"
    else:
        color = discord.Color.red()
        text = "No auto roles."
    embed = discord.Embed(title="Auto Roles", description=text, color=color, timestamp=datetime.datetime.now())
    return embed


async def create(db: asyncpg.pool.Pool, role: discord.Role):
    pass


class AutoGuildRoles(commands.Cog):
    """Commands related to automatic roles being given when a user joins"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @commands.hybrid_group(name="autoroles", description="Auto role management commands", fallback="list")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    @beta.is_beta()
    async def autoroles(self, ctx: commands.Context):
        await ctx.send(embed=await get_embed(self.db, guild=ctx.guild))

    @autoroles.command(name="create", aliases=["add"], description="Create a role to be assigned when users join the server")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    @beta.is_beta()
    async def create(self, ctx: commands.Context):
        view = AddAutoRoleSelect()
        view.db = self.db
        view.original_author = ctx.author
        view.message = await ctx.send(content="Select roles to add to auto roles.", view=view)

    @autoroles.command(
        name="delete", aliases=["remove"], description="Remove an auto role from being assigned when users join your server"
    )
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    @beta.is_beta()
    async def delete(self, ctx: commands.Context):
        view = RemoveAutoRoleSelect()
        view.db = self.db
        view.original_author = ctx.author
        view.message = await ctx.send(content="Select roles to remove from auto roles.", view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        results = await self.db.fetch("SELECT * FROM autoroles WHERE guildid=$1", member.guild.id)
        if results:
            for entry in results:
                r = member.guild.get_role(entry["role"])
                await member.add_roles(r, reason="Assigning auto roles.")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        results = await self.db.fetchrow("SELECT * FROM autoroles WHERE role=$1", role.id)
        if results:
            await self.db.execute("DELETE FROM autoroles WHERE role=$1", role.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoGuildRoles(bot))
