import datetime

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


def is_ticket_channel():
    def predicate(ctx: commands.Context):
        if isinstance(ctx.channel, discord.Thread) and ctx.channel.parent.id == 1131768501330251938:
            return True
        raise commands.CheckFailure("This command must be ran in a help thread.")

    return commands.check(predicate)


def can_give_support():
    def predicate(ctx: commands.Context):
        if ctx.author.guild_permissions.administrator:
            return True
        roles = ["Head Administrator", "Administrator", "admin perms", "*"]
        if any(
            ctx.author.get_role(item) is not None
            if isinstance(item, int)
            else discord.utils.get(ctx.author.roles, name=item) is not None
            for item in roles
        ):
            return True
        raise commands.MissingAnyRole(list(roles))

    return commands.check(predicate)


class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    async def cog_check(self, ctx: commands.Context):
        if ctx.guild and ctx.guild.id == 1120505743913791528:
            return True
        raise commands.CheckFailure("This must be ran in DogKnife Development.")

    async def cog_load(self):
        self.ticketchannel: discord.TextChannel = self.bot.get_channel(1131768501330251938)
        self.logs: discord.TextChannel = self.bot.get_channel(1131779910193664041)

    @commands.hybrid_command(name="new", description="Creates a new ticket.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def create_new_ticket(self, ctx: commands.Context):
        await ctx.typing()
        result = await self.db.fetch("SELECT * FROM tickets")
        number = len(result) + 1
        thread: discord.Thread | None = await self.ticketchannel.create_thread(
            name=f"Ticket Number {number}", reason="User requested a help thread."
        )
        await ctx.send(f"A help thread has been created! {thread.mention}", ephemeral=True)
        embed = (
            discord.Embed(
                title="Welcome to your thread!",
                description="""Thank you for opening a ticket!
                        Help will arrive shortly.
                        In the mean time, please explain your issue.
                        Do not start pinging staff.
                        Be patient or this ticket will be closed.""",
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.now(),
            )
            .set_footer(text="Dog Knife's The Manager")
            .set_author(name=ctx.author.name, icon_url=ctx.author.guild_avatar or ctx.author.display_avatar)
        )
        await thread.add_user(ctx.author)
        message = await thread.send(embed=embed)
        await message.pin()

        await self.db.execute(
            "INSERT INTO tickets (owner, threadid, ticketno, open) VALUES($1, $2, $3, $4)",
            ctx.author.id,
            thread.id,
            number,
            True,
        )
        await self.logs.send(
            f"Ticket #{number}\nNew user help thread for {ctx.author.mention} ({ctx.author.name} {ctx.author.id})-> {thread.mention} ({thread.name})",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command(name="close", description="Closes a help thread.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @is_ticket_channel()
    async def close_ticket(self, ctx: commands.Context):
        await ctx.send("Closing...")
        await ctx.typing()
        await ctx.channel.edit(locked=True, archived=True)
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE threadid=$1", ctx.channel.id)
        await self.db.execute("UPDATE tickets SET OPEN=False")
        await self.logs.send(
            f"Ticket number {data['ticketno']}\nUser {ctx.author.mention} ({ctx.author.name} {ctx.author.id}) has closed {ctx.channel.mention} ({ctx.channel.name})\nTicket Author: {ctx.bot.get_user(data['owner']).mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command(name="join", description="Joins a ticket.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @can_give_support()
    @app_commands.describe(thread_number="The ticket number. NOT the ID. This is obtainable in ticket logs.")
    @app_commands.rename(thread_number="thread")
    async def join_user_ticket(self, ctx: commands.Context, thread_number: int):
        await ctx.typing()
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE ticketno=$1", thread_number)
        if data and data["open"]:
            channel: discord.Thread | None = self.ticketchannel.get_thread(data["threadid"])
            await channel.add_user(ctx.author)
            await ctx.send(content=f"Joined. You may access it here: {channel.mention}", ephemeral=True)
        else:
            await ctx.edit_original_response("Ticket Number was not found, or this ticket is already closed.")

    @commands.hybrid_command(name="leave", description="Lets staff leave a ticket.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @app_commands.describe(thread_number="The ticket number to leave.")
    @app_commands.rename(thread_number="thread")
    async def leave_user_ticket(self, ctx: commands.Context, thread_number: int):
        await ctx.typing()
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE ticketno=$1", thread_number)
        if data and data["owner"] != ctx.author.id:
            channel: discord.Thread | None = self.ticketchannel.get_thread(data["threadid"])
            await channel.remove_user(ctx.author)
        await ctx.send("You have left the ticket.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot), guilds=[discord.Object(id=1120505743913791528)])
