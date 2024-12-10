import discord
from discord.ext import commands


class Stfu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.embeds[0].footer.text == "Boost the support server to never see this again: /invite":
            await message.delete()


async def setup(bot):
    await bot.add_cog(Stfu(bot))
