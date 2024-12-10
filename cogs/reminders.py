import datetime
from typing import Union

import asyncpg
import discord
from discord import ui
from discord.ext import commands, tasks


class UrlView(ui.View):
    def __init__(self, message: Union[discord.Message, discord.WebhookMessage]):
        self.message = message
        self.add_item(ui.Button(label="Original Message", url=message.jump_url))


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @tasks.loop()
    async def send_reminder(self) -> tasks.loop:
        next_task: asyncpg.Record | None = await self.db.fetchrow(
            "SELECT * FROM tasks WHERE COMPLETED=False ORDER BY time LIMIT 1;"
        )
        if next_task is None:
            self.send_reminder.stop()
            return

        time = datetime.datetime.replace(next_task["time"], tzinfo=datetime.timezone.utc)
        await discord.utils.sleep_until(time)
        channel = self.bot.get_channel(next_task["channel_id"])
        author = self.bot.get_user(next_task["owner_id"])
        if next_task["message_id"]:
            view = UrlView(next_task["message_id"])
        else:
            view = None
        await channel.send(f"{author.mention}\n{next_task['name']}", view=view)

        await self.db.execute(
            "DELETE FROM tasks WHERE time=$1 AND name=$2 AND channel_id=$3 AND owner_id=$4",
            next_task["time"],
            next_task["name"],
            next_task["channel_id"],
            next_task["owner_id"],
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
