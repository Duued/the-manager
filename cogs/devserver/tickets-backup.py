import datetime

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


def is_ticket_channel():
    def predicate(interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.Thread) and interaction.channel.parent.id == 1131768501330251938:
            return True
        raise app_commands.CheckFailure("This command must be ran in a help thread.")

    return app_commands.check(predicate)


def can_give_support():
    def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        roles = ["Head Administrator", "Administrator", "admin perms", "*"]
        if any(
            interaction.user.get_role(item) is not None
            if isinstance(item, int)
            else discord.utils.get(interaction.user.roles, name=item) is not None
            for item in roles
        ):
            return True
        raise app_commands.MissingAnyRole(list(roles))

    return app_commands.check(predicate)


class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db
        self.ticketchannel: discord.TextChannel = bot.get_channel(1131768501330251938)
        self.logs: discord.TextChannel = bot.get_channel(1131779910193664041)

    @commands.hybrid_command(name="new", description="Creates a new ticket.")
    async def create_new_ticket(self, interaction: discord.Interaction):
        result = await self.db.fetch("SELECT * FROM tickets")
        number = len(result) + 1
        thread: discord.Thread | None = await self.ticketchannel.create_thread(
            name=f"Ticket Number {number}", reason="User requested a help thread."
        )
        await interaction.response.send_message(f"A help thread has been created! {thread.mention}", ephemeral=True)
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
            .set_author(
                name=interaction.user.name, icon_url=interaction.user.guild_avatar or interaction.user.display_avatar
            )
        )
        await thread.add_user(interaction.user)
        message = await thread.send(embed=embed)
        await message.pin()

        await self.db.execute(
            "INSERT INTO tickets (owner, threadid, ticketno, open) VALUES($1, $2, $3, $4)",
            interaction.user.id,
            thread.id,
            number,
            True,
        )
        await self.logs.send(
            f"Ticket #{number}\nNew user help thread for {interaction.user.mention} ({interaction.user.name} {interaction.user.id})-> {thread.mention} ({thread.name})",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command(name="close", description="Closes a help thread.")
    @is_ticket_channel()
    async def close_ticket(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing...")
        await interaction.channel.edit(locked=True, archived=True)
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE threadid=$1", interaction.channel.id)
        await self.db.execute("UPDATE tickets SET OPEN=False")
        await self.logs.send(
            f"Ticket number {data['ticketno']}\nUser {interaction.user.mention} ({interaction.user.name} {interaction.user.id}) has closed {interaction.channel.mention} ({interaction.channel.name})\nTicket Author: {interaction.client.get_user(data['owner']).mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command(name="join", description="Joins a ticket.")
    @can_give_support()
    @app_commands.describe(thread_number="The ticket number. NOT the ID. This is obtainable in ticket logs.")
    @app_commands.rename(thread_number="thread")
    async def join_user_ticket(self, interaction: discord.Interaction, thread_number: int):
        await interaction.response.defer(ephemeral=True)
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE ticketno=$1", thread_number)
        if data and data["open"]:
            channel: discord.Thread | None = self.ticketchannel.get_thread(data["threadid"])
            await channel.add_user(interaction.user)
            await interaction.followup.send(content=f"Joined. You may access it here: {channel.mention}", ephemeral=True)
            await interaction.delete_original_response()
        else:
            await interaction.edit_original_response("Ticket Number was not found, or this ticket is already closed.")

    @commands.hybrid_command(name="leave", description="Lets staff leave a ticket.")
    @app_commands.describe(thread_number="The ticket number to leave.")
    @app_commands.rename(thread_number="thread")
    async def leave_user_ticket(self, interaction: discord.Interaction, thread_number: int):
        await interaction.response.defer(ephemeral=True)
        data = await self.db.fetchrow("SELECT * FROM tickets WHERE ticketno=$1", thread_number)
        if data and data["owner"] != interaction.user.id:
            channel: discord.Thread | None = self.ticketchannel.get_thread(data["threadid"])
            await channel.remove_user(interaction.user)
        await interaction.followup.send("You have left the ticket.", ephemeral=True)
        await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(Tickets(bot), guilds=[discord.Object(id=1120505743913791528)])
