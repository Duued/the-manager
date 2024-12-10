import datetime
import random
import re
from typing import Union

import asyncpg
import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands

from cogs import beta


_cd = app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)
_cd2 = app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)


class CogMissingError(Exception):
    def __init__(self, msg):
        pass


async def create_reminder(
    self,
    cog: commands.Cog | None,
    db: asyncpg.pool.Pool,
    reminder_name: str,
    *,
    user_id: int,
    channel_id: int,
    time: datetime.datetime,
):
    if cog is None:
        CogMissingError("The reminder cog was not found. Cannot create reminder.")
    await db.execute(
        "INSERT INTO tasks(name, channel_id, owner_id, time) VALUES($1, $2, $3, $4)",
        reminder_name,
        channel_id,
        user_id,
        time,
    )
    send_reminder = cog.send_reminder
    if send_reminder.is_running():
        send_reminder.restart()
    else:
        send_reminder.start()


class StoreAutoComplete:
    def __init__(self, db: asyncpg.pool.Pool):
        self.db = db

    async def store_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        options = self.db.fetch("SELECT name FROM items")
        return [app_commands.Choice(name=option, value=option) for option in options if current.lower() in option.lower()]


async def add_cash(db: asyncpg.pool.Pool, *, user_id: int, amount: int):
    await db.execute(
        "INSERT INTO economy(user_id, cash) VALUES($1, $2) ON CONFLICT(user_id) DO UPDATE SET user_id=$1, cash=economy.cash+$2;",
        user_id,
        amount,
    )


async def remove_cash(db: asyncpg.pool.Pool, *, user_id: int, amount: int):
    cash: int | None = await db.fetchval("SELECT cash FROM economy WHERE user_id=$1", user_id)
    if cash:
        new_amount = cash - amount
        await db.execute(
            "UPDATE economy SET user_id=$1, cash=$2 WHERE user_id=$1",
            user_id,
            new_amount,
        )


async def modify_cash(db: asyncpg.pool.Pool, *, user_id: int, amount: int):
    await db.execute(
        "INSERT INTO economy(user_id, cash) VALUES($1, $2) ON CONFLICT(user_id) DO UPDATE SET user_id=$1, cash=$2;",
        user_id,
        amount,
    )


async def get_cash(db: asyncpg.pool.Pool, user_id: int):
    return await db.fetchval("SELECT cash FROM economy WHERE user_id=$1", user_id)


async def rob_logic(
    db: asyncpg.pool.Pool, for_who: Union[discord.Member, discord.User], target_user: Union[discord.Member, discord.User]
) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.red(), title="Robbery Failed", timestamp=datetime.datetime.now())
    target_id = target_user.id
    if for_who.id == target_id:
        embed.description = ":x: You cannot rob yourself lmao."
        return embed
    cash: int | None = await db.fetchval("SELECT cash FROM economy WHERE user_id=$1", target_id)
    my_cash: int | None = await db.fetchval("SELECT cash FROM economy WHERE user_id=$1", for_who.id)
    if my_cash and my_cash > 0:
        if cash and cash == 0:
            embed.description = ":x: This user cannot be robbed. They have no money."
        elif not cash:
            embed.description = ":x: This user cannot be robbed. They are not in the economy database."
        else:
            choice = random.randint(1, 10)
            if choice <= 3:
                fine = choice * 12 * random.randint(1, 4)
                embed.description = (
                    f"You attempted to rob {target_user.mention} but caught. You paid :dollar: {fine} in fines."
                )
                await remove_cash(db, user_id=for_who.id, amount=fine)
            else:
                amount = choice * random.randint(6, 14) * random.randint(1, 4)
                user_bal = await get_cash(db, target_id)
                if amount > user_bal:
                    embed.description = f"You would've robbed :dollar: {amount} from {target_user.mention} but their balance is {user_bal}\nLmao"
                else:
                    embed.description = f"You have successfully robbed :dollar: {amount} from {target_user.mention}."
                    embed.title = "Robbery Success"
                    embed.color = discord.Color.green()
                    await add_cash(db, user_id=for_who.id, amount=amount)
                    await remove_cash(db, user_id=target_id, amount=amount)
    else:
        embed.description = ":x: You have no money. You can </work:1141434507115888650> to earn some!"
    return embed


async def do_rob(db: asyncpg.pool.Pool, interaction: discord.Interaction, target_user: Union[discord.Member, discord.User]):
    embed = await rob_logic(db, interaction.user, target_user)
    await interaction.response.send_message(embed=embed)


async def force_do_rob(
    db: asyncpg.pool.Pool,
    ctx: commands.Context,
    for_who: Union[discord.Member, discord.User],
    target_user: Union[discord.Member, discord.User],
):
    embed = await rob_logic(db, for_who, target_user)
    await ctx.send("(Force robbery result)", embed=embed)


async def do_work(
    db: asyncpg.pool.Pool,
    interaction_ctx: Union[discord.Interaction, commands.Context],
    who: Union[discord.Member, discord.User] = None,
):
    profit = random.randint(45, 110)
    profit *= random.randint(1, 2)
    if isinstance(interaction_ctx, discord.Interaction):
        interaction = interaction_ctx
        await add_cash(db, user_id=interaction.user.id, amount=profit)
        embed = discord.Embed(
            title="Work Result",
            description=f"You worked and received :dollar: {profit}!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )
        await interaction.response.send_message(embed=embed)
    else:
        if not who:
            raise commands.MissingRequiredArgument(who)
        ctx = interaction_ctx
        await add_cash(db, user_id=who.id, amount=profit)
        embed = discord.Embed(
            title="Work Result",
            description=f"{who.mention} was force-worked and received :dollar: {profit}!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )
        await ctx.send(embed=embed)


async def do_crime(
    db: asyncpg.pool.Pool,
    interaction_ctx: Union[discord.Interaction, commands.Context],
    who: Union[discord.Member, discord.User] = None,
):
    amount = random.randint(100, 250)
    to_multiply_by = random.randint(6, 8)
    if isinstance(interaction_ctx, discord.Interaction):
        interaction = interaction_ctx
        choice = random.randint(1, 10)
        if choice < 5:
            amount *= random.randint(4, 6)
            embed = discord.Embed(
                title="Crime Result",
                description=f"You got caught attempting to rob a bank.\nYou paid :dollar: {amount} in fines",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            await remove_cash(db, user_id=interaction.user.id, amount=amount)
            await interaction.response.send_message(embed=embed)
        else:
            amount *= to_multiply_by
            await add_cash(db, user_id=interaction.user.id, amount=amount)
            embed = discord.Embed(
                title="Crime Result",
                description=f"You successfully robbed :dollar: {amount} from a bank!",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(),
            )
            await interaction.response.send_message(embed=embed)
    else:
        if not who:
            raise commands.MissingRequiredArgument(who)
        ctx = interaction_ctx
        choice = random.randint(1, 10)
        if choice <= 5:
            embed = discord.Embed(
                title="Crime Result",
                description=f"You got caught attempting to rob a bank.\nYou paid :dollar: {amount} in fines",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            await remove_cash(db, user_id=who.id, amount=amount)
            await ctx.send("Force rob result", embed=embed)
        else:
            await add_cash(db, user_id=who.id, amount=amount)
            embed = discord.Embed(
                title="Work Result",
                description=f"{who.mention} robbed a bank for :dollar: {amount}!",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(),
            )
            await ctx.send("Force rob result", embed=embed)


async def get_leaderboard(db: asyncpg.pool.Pool) -> list[asyncpg.Record]:
    return await db.fetch("SELECT * FROM economy ORDER BY cash DESC LIMIT 10;")


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db
        self.rob_user_ctx_menu = app_commands.ContextMenu(name="Rob", callback=self.rob_menu)
        self.get_user_balance = app_commands.ContextMenu(name="Balance", callback=self.balance_menu)
        self.bot.tree.add_command(self.rob_user_ctx_menu)
        self.bot.tree.add_command(self.get_user_balance)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.rob_user_ctx_menu.name, type=self.rob_user_ctx_menu.type)
        self.bot.tree.remove_command(self.get_user_balance.name, type=self.get_user_balance.type)

    @app_commands.command(name="work", description="Work for money")
    @beta.is_beta_i()
    @checks.cooldown(1, 600, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        await do_work(self.db, interaction)
        new_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        config_key = await self.db.fetchval(
            "SELECT work_notifications FROM userconfig WHERE user_id=$1", interaction.user.id
        )
        if config_key is None or config_key is False:
            return
        await self.db.execute(
            "INSERT INTO tasks(name, channel_id, owner_id, time) VALUES($1, $2, $3, $4)",
            "Work again!",
            interaction.channel.id,
            interaction.user.id,
            new_time,
        )
        c = self.bot.get_cog("Reminder")
        send_reminder = c.send_reminder
        if send_reminder:
            if send_reminder.is_running():
                send_reminder.restart()
            else:
                send_reminder.start()

    @app_commands.command(name="balance", description="Get a user or your own balance")
    @app_commands.describe(user="Who are you getting the balance for? Leaving this blank defaults to you")
    @beta.is_beta_i()
    @checks.cooldown(2, 10, key=lambda i: i.user.id)
    async def user_balance(self, interaction: discord.Interaction, user: Union[discord.Member, discord.User] = None):
        user = user or interaction.user
        cash = await get_cash(self.db, user.id)
        embed = discord.Embed(title=f"Balance for {user.name}")
        if cash and cash > 0:
            embed.description = f":dollar: {cash}"
            embed.color = discord.Color.green()
        elif cash and cash <= 0:
            embed.description = f":dollar: {cash}\nLmao"
            embed.color = discord.Color.red()
        else:
            embed.description = ":dollar: 0\nLmao"
            embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed)

    @beta.is_beta_i()
    @checks.cooldown(2, 10, key=lambda i: i.user.id)
    async def balance_menu(self, interaction: discord.Interaction, member: discord.Member):
        user = member
        cash = await get_cash(self.db, user.id)
        embed = discord.Embed(title=f"Balance for {user.mention}")
        if cash and cash > 0:
            embed.description = f":dollar: {cash}"
            embed.color = discord.Color.green()
        elif cash and cash <= 0:
            embed.description = f":dollar: {cash}\nLmao"
            embed.color = discord.Color.red()
        else:
            embed.description = (
                f"{user.mention} is not in the economy system. They can </work:1141434507115888650> to get started!"
            )
            embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="donate", description="Donate some cash to a user!")
    @app_commands.describe(user="Who recieves the money?", cash="How much cash are you giving them?")
    @app_commands.rename(cash="amount")
    @beta.is_beta_i()
    @checks.cooldown(1, 300, key=lambda i: i.user.id)
    async def payout(self, interaction: discord.Interaction, user: Union[discord.Member, discord.User], cash: int):
        embed = discord.Embed(title="Payout result.")
        if await get_cash(self.db, interaction.user.id) < cash:
            embed.description = "Payout failed. You attempted to give more than you have!"
            embed.color = discord.Color.red()
        elif cash <= 0:
            embed.description = "Payout failed. Cash must be `1` or greater."
            embed.color = discord.Color.red()
        else:
            await remove_cash(self.db, user_id=interaction.user.id, amount=cash)
            await add_cash(self.db, user_id=user.id, amount=cash)
            embed.description = f"Successfully gave {user.mention} :dollar: {cash}!"
            embed.color = discord.Color.green()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rob", description="Attempt to rob a user.")
    @app_commands.describe(user="Who you are attempting to rob from")
    @_cd2
    @beta.is_beta_i()
    async def rob_user(self, interaction: discord.Interaction, user: Union[discord.Member, discord.User]):
        await do_rob(self.db, interaction, user)
        config_key = await self.db.fetchval("SELECT rob_notifications FROM userconfig WHERE user_id=$1", interaction.user.id)
        if config_key is None or config_key is False:
            return
        new_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        await self.db.execute(
            "INSERT INTO tasks(name, channel_id, owner_id, time) VALUES($1, $2, $3, $4)",
            "Rob again!",
            interaction.channel.id,
            interaction.user.id,
            new_time,
        )
        c = self.bot.get_cog("Reminder")
        send_reminder = c.send_reminder
        if send_reminder:
            if send_reminder.is_running():
                send_reminder.restart()
            else:
                send_reminder.start()

    @_cd2
    @beta.is_beta_i()
    async def rob_menu(self, interaction: discord.Interaction, member: discord.Member):
        await do_rob(self.db, interaction, member)
        config_key = await self.db.fetchval("SELECT rob_notifications FROM userconfig WHERE user_id=$1", interaction.user.id)
        if config_key is None or config_key is False:
            return
        new_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        await self.db.execute(
            "INSERT INTO tasks(name, channel_id, owner_id, time) VALUES($1, $2, $3, $4)",
            "Work again!",
            interaction.channel.id,
            interaction.user.id,
            new_time,
        )
        c = self.bot.get_cog("Reminder")
        send_reminder = c.send_reminder
        if send_reminder:
            if send_reminder.is_running():
                send_reminder.restart()
            else:
                send_reminder.start()

    @app_commands.command(name="leaderboard", description="Gets the cash leaderboard")
    @checks.cooldown(1, 10, key=lambda i: i.user.id)
    @beta.is_beta_i()
    async def view_leaderboard(self, interaction: discord.Interaction):
        text = ""
        rows = await get_leaderboard(self.db)
        counter = 1
        for row in rows:
            user = interaction.client.get_user(row["user_id"])
            if user:
                text += f"{counter}. {user.mention}'s Cash: :dollar: {row['cash']}\n"
            else:
                temporary_user = await self.bot.fetch_user(row["user_id"])
                match_result = re.match(r"Deleted User [a-f0-9]{8}", temporary_user.name)  # Discord get yo shit together
                # See this thread for details https://discord.com/channels/336642139381301249/1192584851111546980
                if match_result:  # Account is deleted (probably)
                    await self.db.execute("DELETE FROM economy WHERE user_id=$1", row["user_id"])
                print(f"{user} was not found. ({row['user_id']})")
            counter += 1
        embed = discord.Embed(
            title="Leaderboard", description=text, color=discord.Color.green(), timestamp=datetime.datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="crime", description="Commit a crime. This rewards more than work but also has more penalty than work."
    )
    @checks.cooldown(1, 600, key=lambda i: i.user.id)
    @beta.is_beta_i()
    async def crime(self, interaction: discord.Interaction):
        await do_crime(self.db, interaction)
        config_key = await self.db.fetchval(
            "SELECT crime_notifications FROM userconfig WHERE user_id=$1", interaction.user.id
        )
        if config_key is None or config_key is False:
            return
        new_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        await self.db.execute(
            "INSERT INTO tasks(name, channel_id, owner_id, time) VALUES($1, $2, $3, $4)",
            "Crime time!",
            interaction.channel.id,
            interaction.user.id,
            new_time,
        )
        c = self.bot.get_cog("Reminder")
        send_reminder = c.send_reminder
        if send_reminder:
            if send_reminder.is_running():
                send_reminder.restart()
            else:
                send_reminder.start()

    # shop = app_commands.Group(name="shop", description="The global economy shop commands")

    # @shop.command(name="items", description="Lists items avaliable for purchase")
    # @beta.is_beta_i()
    # @checks.cooldown(1, 10, key=lambda i: i.user.id)
    # async def list_shop_items(self, interaction: discord.Interaction):
    #    results = self.db.execute("SELECT * FROM items")
    #    text = ""
    #    counter = 1
    #    for result in results:
    #        text += f"{counter}. `{result['name']}\n"
    #    embed = discord.Embed(title="Economy shop items.", description=text, timestamp=datetime.datetime.now(), color=0x7289da)
    #    await interaction.response.send_message(embed=embed)
    #
    # @shop.command(name="purchase", description="Purchase an item")

    @commands.group(name="cashmod", invoke_without_command=True)
    @commands.is_owner()
    async def cashmod_group(self, ctx: commands.Context, user: Union[discord.Member, discord.User], amount: int):
        """Set a user's cash.

        This command group also has commands to reset, force rob, force work, and do much more."""
        await modify_cash(self.db, user_id=user.id, amount=amount)
        embed = discord.Embed(
            title="Cash Mod Result",
            description=f"{user.mention}'s cash has been set to {amount}.",
            color=0x7289DA,
            timestamp=datetime.datetime.now(),
        )
        await ctx.send(embed=embed)

    @cashmod_group.command()
    @commands.is_owner()
    async def reset(self, ctx: commands.Context, user: Union[discord.Member, discord.User]):
        """Reset a specific user's cash."""
        await modify_cash(self.db, user_id=user.id, amount=0)
        embed = discord.Embed(
            title="Cash Mod Result",
            description=f"{user.mention}'s cash has been reset.",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        await ctx.send(embed=embed)

    @cashmod_group.command(name="work")
    @commands.is_owner()
    async def force_work(self, ctx: commands.Context, user: Union[discord.Member, discord.User]):
        """Force work for a user"""
        await do_work(self.db, ctx, user)

    @cashmod_group.command(name="rob")
    @commands.is_owner()
    async def force_rob(
        self,
        ctx: commands.Context,
        for_who: Union[discord.Member, discord.User],
        target: Union[discord.Member, discord.User],
    ):
        """Forces a robbery"""
        await force_do_rob(self.db, ctx, for_who, target)

    @cashmod_group.command(name="add")
    @commands.is_owner()
    async def add_cash(self, ctx: commands.Context, user: Union[discord.Member, discord.User], amount: int):
        """Add cash to a user"""
        await add_cash(self.db, user_id=user.id, amount=amount)
        embed = discord.Embed(
            title="Cash Mod Result",
            description=f"{amount} was added to {user.mention}'s cash",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )
        await ctx.send(embed=embed)

    @cashmod_group.command(name="subtract", aliases=["remove", "sub"])
    @commands.is_owner()
    async def remove_cash(self, ctx: commands.Context, user: Union[discord.Member, discord.User], amount: int):
        """Subtract cash from a user"""
        await remove_cash(self.db, user_id=user.id, amount=amount)
        embed = discord.Embed(
            title="Cash Mod Result",
            description=f"{amount} was removed from {user.mention}'s cash",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        await ctx.send(embed=embed)

    @cashmod_group.command(name="crime")
    @commands.is_owner()
    async def force_crime(self, ctx: commands.Context, user: discord.User):
        """Forces a user to commit a crime"""
        await do_crime(self.db, ctx, user)

    @cashmod_group.command(name="ban")
    @commands.is_owner()
    async def economy_ban(self, ctx: commands.Context, user: discord.User):
        """Bans a user from using economy.

        This technically isn't actually a ban command, it sets their cash so low it'd be impossible to work back."""
        amount = -999999999999999999
        await modify_cash(self.db, user_id=user.id, amount=amount)
        embed = discord.Embed(
            title="Economy Ban Result",
            description=f"{user.mention} has had their cash set to {amount}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @cashmod_group.command(name="transfer")
    @commands.is_owner()
    async def trasnfer_cash(self, ctx: commands.Context, user_from: discord.User, user_to: discord.User, amount: int):
        """Transfers money from someone to someone else

        user_from - The user to take cash from
        user_to - The user to give the cash to
        amount - The amount of cash to transfer
        """
        await remove_cash(self.db, user_id=user_from.id, amount=amount)
        await add_cash(self.db, user_id=user_to.id, amount=amount)
        embed = discord.Embed(
            title="Transfer money result",
            description=f"Transfered {amount} money from {user_from.name} ({user_from.id}) to {user_to.name} ({user_to.id})",
            color=0x0075FF,
        )
        await ctx.send(embed=embed)

    @cashmod_group.command(name="clean")
    @commands.is_owner()
    async def economy_clean(self, ctx: commands.Context, purge_deleted_users: bool=True, purge_no_shared_guilds: bool=True):
        embed = discord.Embed(title="Economy clean.", description="Beginning economy clean\nLocking bot\n", color=discord.Color.red())
        msg = await ctx.send(embed=embed)
        self.bot.locked = True
        removeda = 0
        removedb = 0
        embed.description += "Bot locked\n"
        await msg.edit(embed=embed)
        if purge_deleted_users:
            embed.description += "Begin purge deleted users\n"
            await msg.edit(embed=embed)
            embed.description += "Fetching leaderboard and purging...\n"
            rows = await get_leaderboard(self.db)
            counter = 1
            
            await msg.edit(embed=embed)
            for row in rows:
                user = ctx.bot.get_user(row["user_id"])
                if not user:
                    temporary_user = await self.bot.fetch_user(row["user_id"])
                    match_result = re.match(r"Deleted User [a-f0-9]{8}", temporary_user.name)  # Discord get yo shit together
                    # See this thread for details https://discord.com/channels/336642139381301249/1192584851111546980
                    if match_result:  # Account is deleted (probably)
                        removeda += 1
                        await self.db.execute("DELETE FROM economy WHERE user_id=$1", row["user_id"])
                    print(f"{user} was not found. ({row['user_id']})")
                counter += 1
            embed.description += f"Deleted user purge complete. Removed {removeda} users.\n"
            await msg.edit(embed=embed)
        if purge_no_shared_guilds:
            embed.description += "Begin purge no mutual guild users\n"
            await msg.edit(embed=embed)
            embed.description += "Fetch leaderboard and begin purging\n"
            await msg.edit(embed=embed)
            rows = await self.db.fetch("SELECT * FROM economy ORDER BY cash DESC;")
            counter = 1
            removedb = 0
            for row in rows:
                user = ctx.bot.get_user(row["user_id"])
                if user and len(user.mutual_guilds) == 0:
                    removedb += 1
                    await self.db.execute("DELETE FROM economy WHERE user_id=$1", row["user_id"])
                    print(f"{user} has no mutual guilds. ({row['user_id']})")
                elif not user:
                    tempuser = await ctx.bot.fetch_user(row['user_id'])
                    if tempuser and len(tempuser.mutual_guilds) == 0:
                        removedb += 1
                        await self.db.execute("DELETE FROM economy WHERE user_id=$1", row["user_id"])
                        print(f"{user} has no mutual guilds. ({row['user_id']})")
                counter += 1
            embed.description += f"No mutual guild purge complete. Removed {removedb} users.\n"
            await msg.edit(embed=embed)
        embed.description += f"Purge complete. Removed {removeda + removedb} total users.\n"
        await msg.edit(embed=embed)
        self.bot.locked = False
        embed.description += "Bot unlocked.\n"
        await msg.edit(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
