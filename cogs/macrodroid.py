import aiohttp
from discord.ext import commands


def get_hook(send_type: str) -> str:
    return f"https://trigger.macrodroid.com/e15496c7-036e-4582-bde5-2ab24fab087c/online?type={send_type}"


def is_family_member():
    async def check(ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):  # Future conditions can go here...
            return True
        raise commands.CheckFailure("This command is restricted to family members.")

    return commands.check(check)


class MacroDroid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="meal", aliases=["dinner"])
    @is_family_member()
    async def meal_macrodroid_notification(self, ctx: commands.Context):
        """Push a notification to family members about a meal being ready."""
        async with aiohttp.ClientSession() as session:
            await session.get(get_hook("meal"))
        await ctx.reply("Notification pushed.", mention_author=False)

    @commands.command(name="attention", aliases=["alert"])
    @is_family_member()
    async def alert_macrodroid_notification(self, ctx: commands.Context):
        """Push a notification to very specific family members. Cannot be configured."""
        async with aiohttp.ClientSession() as session:
            await session.get(get_hook("attention"))
        await ctx.reply("Notification pushed", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MacroDroid(bot))
