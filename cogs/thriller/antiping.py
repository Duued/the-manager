import datetime
from typing import Union

import discord
from discord.ext import commands


def ignored_roles(member: discord.Member, roles: list[Union[str, int, discord.Role]]):
    """Check on message author is exempt from anti ping."""
    for member_role in member.roles:
        for role in roles:
            if isinstance(role, discord.Role):
                if member_role.id == role.id:
                    return True
            elif isinstance(role, int):
                if member_role.id == role:
                    return True
            else:
                if discord.utils.get(member.roles, name=role):
                    return True
    return False


class AntiPing(commands.Cog):
    """Cog class."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.thriller_guild: discord.Guild | None = None
        self.thriller_member: discord.Member | None = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Check message on send."""
        if not self.thriller_guild:
            self.thriller_guild = self.bot.get_guild(589629614419345424)
        if not self.thriller_member:
            self.thriller_member = self.thriller_guild.get_member(448662670900461568)
        if message.guild != self.thriller_guild:
            return
        if self.thriller_member in message.mentions:
            if self.thriller_member.mention not in message.content:
                return
            roles = [938319505153728513, 679536428316622907, 810667533757579275]
            if ignored_roles(message.author, roles):
                return
            if message.author.bot:
                return
            embed = discord.Embed(title="Ping Warning", color=discord.Color.red())
            embed.description = """Hey there, please refrain from pinging Thriller unnecessarily. 
            While it is okay sometimes, it can get very annoying quickly. Thank you!"""
            embed.timestamp = datetime.datetime.now()
            await message.reply(embed=embed, mention_author=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiPing(bot))
