import io

import asyncpg
import discord
from discord.ext import commands


class Sql(commands.Cog):
    """The SQL Command Cog.

    Owner Only"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.Pool = bot.db

    async def cog_check(self, ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner(f"You must own this bot to use {ctx.command.name}")

    @commands.group(name="sql", aliases=["s", "db"], invoke_without_command=True, brief="Execute SQL.")
    async def sql_group(self, ctx: commands.Context, *, query: str):
        """Execute a SQL query

        This is a command group
        """
        strategy = self.db.execute
        results = await strategy(query)
        await ctx.reply(results, mention_author=False)

    @sql_group.command(name="fetch", brief="Fetch SQL.")
    async def sql_fetch(self, ctx: commands.Context, *, query: str):
        results = await self.db.fetch(query)
        await ctx.reply(results, mention_author=False)

    @sql_group.command(name="fetchrow", brief="Fetchrow SQL.")
    async def sql_fetchrow(self, ctx: commands.Context, *, query: str):
        results = await self.db.fetchrow(query)
        await ctx.reply(results, mention_author=False)

    @sql_group.command(name="fetchval", brief="Fetchval SQL.")
    async def sql_fetchval(self, ctx: commands.Context, *, query: str):
        results = await self.db.fetchval(query)
        await ctx.reply(results, mention_author=False)

    @sql_group.command(name="csv", brief="Returns output into a CSV file")
    async def sql_csv(self, ctx: commands.Context, dm: commands.Greedy[bool] = False, *, full_query: str):
        fp = io.BytesIO()
        await self.db.copy_from_query(full_query, output=fp, format="csv", header=True)
        fp.seek(0)
        if dm:
            destination = ctx.author
        else:
            destination = ctx
        await destination.send(file=discord.File(fp, filename="results.csv"))

    @sql_group.command(name="csv-table", brief="Returns output into a CSV file")
    async def sql_csv_table(self, ctx: commands.Context, dm: commands.Greedy[bool] = False, *, full_query: str):
        fp = io.BytesIO()
        await self.db.copy_from_table(full_query, output=fp, format="csv", header=True)
        fp.seek(0)
        if dm:
            destination = ctx.author
        else:
            destination = ctx
        await destination.send(file=discord.File(fp, filename="results.csv"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Sql(bot))
