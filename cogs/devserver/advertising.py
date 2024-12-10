import datetime

import asyncpg
import discord
from discord.ext import commands, tasks


class Advertising(commands.Cog):
    guild: discord.Guild
    category: discord.CategoryChannel
    cooldown_role: discord.Role

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    async def cog_load(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.get_guild(1120505743913791528)
        self.category = self.bot.get_channel(1143638700543197295)
        self.cooldown_role = self.guild.get_role(1143639861627195483)

    @tasks.loop()
    async def remove_promo_cooldown_role(self) -> tasks.loop:
        next_task: asyncpg.Record | None = await self.db.fetchrow("SELECT * FROM self_promo_task ORDER BY time LIMIT 1;")
        if next_task is None:
            self.remove_promo_cooldown_role.stop()
            return

        time = datetime.datetime.replace(next_task["time"], tzinfo=datetime.timezone.utc)
        await discord.utils.sleep_until(time)
        member: discord.Member | None = self.guild.get_member(next_task["user_id"])
        if member:
            await member.remove_roles(self.cooldown_role, reason="Role timeout ended.")
        await self.db.execute(
            "DELETE FROM self_promo_task WHERE user_id=$1 AND time=$2", next_task["user_id"], next_task["time"]
        )

    @remove_promo_cooldown_role.before_loop
    async def wait_before_task(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.category_id == self.category.id:
            if self.cooldown_role in message.author.roles:
                return
            future_time = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
            await message.author.add_roles(self.cooldown_role, reason="User sent an advertisement.")
            await self.db.execute(
                "INSERT INTO self_promo_task(user_id, time) VALUES($1, $2)", message.author.id, future_time
            )
            if self.remove_promo_cooldown_role.is_running():
                self.remove_promo_cooldown_role.restart()
            else:
                self.remove_promo_cooldown_role.start()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild != self.guild:
            return
        for channel in self.category.channels:
            if channel.id != 1143638769707274323:
                await channel.purge(
                    limit=None, check=lambda m: m.author.id == member.id, reason="User left, ads are being deleted."
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(Advertising(bot))
