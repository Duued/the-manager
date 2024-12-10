import discord
import re
import datetime
import asyncio
from discord.ext import commands

SEE_BIO_REGEX = r"SEE ByIO .{3,}"


class AutoBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name="on_member_join")
    async def autoban(self, member: discord.Member):
        ban = False
        if member.guild.id == 589629614419345424:
            if member.name and re.match(SEE_BIO_REGEX, member.name):
                ban = True
            if member.display_name and re.match(SEE_BIO_REGEX, member.display_name):
                ban = True
            if member.global_name and re.match(SEE_BIO_REGEX, member.global_name):
                ban = True
            if member.nick and re.match(SEE_BIO_REGEX, member.nick):
                ban = True
        if ban:
            await member.ban(reason="[AUTOBAN] - Scam Bot")
            welcome_channel = self.bot.get_channel(1196905697632338071)
            sapphire_log_channel = self.bot.get_channel(1196968955315753020)
            embed = discord.Embed(
                title="AutoBan Result",
                description=f"[AUTOBAN]\n{member.mention}\nName: {member.name}\nDisplay Name:{member.display_name}\nGlobal Name: {member.global_name}\n ID: {member.id}.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            ).set_footer(text="Dog Knife's The Manager")
            await welcome_channel.send(embed=embed)
            await sapphire_log_channel.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await member.ban(await member.ban(reason="[AUTOBAN] - Scam Bot. Sapphire auto removed ban."))
            except:  # noqa: E722
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoBan(bot))