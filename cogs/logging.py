import datetime
import os
import textwrap

import aiohttp
import discord
import dotenv
from discord.ext import commands, tasks

import advancedlogging


dotenv.load_dotenv(verbose=True)


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session
        self.webhook = discord.Webhook.from_url(url=os.getenv("logging_webhook"), session=session)

    async def cog_load(self):
        self.logging_loop.start()

    async def cog_unload(self):
        self.logging_loop.stop()

    @tasks.loop(seconds=0)
    async def logging_loop(self):
        to_log = await self.bot.logging_queue.get()

        timestamp = datetime.datetime.now()

        message = textwrap.shorten(f"{discord.utils.format_dt(timestamp)}\n{to_log.message}", width=1990)

        await self.webhook.send(message, username=self.bot.user.name, avatar_url=self.bot.user.display_avatar)


async def setup(bot: commands.Bot):
    async with aiohttp.ClientSession() as session, advancedlogging.LogHandler(bot=bot) as handler:
        bot.handler = handler
        await bot.add_cog(Logging(bot, session))
