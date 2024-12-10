import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dog", description="Get a random dog picture.")
    async def dog_api_picture(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            response = await fetch(session, "https://dog.ceo/api/breeds/image/random")
            embed = discord.Embed(title="Here's your doggo!", color=0x7289DA)
            embed.set_image(url=response["message"])
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cat", description="Get a random cat picture.")
    async def cat_api_picture(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            response = await fetch(session, "https://api.thecatapi.com/v1/images/search")
            embed = discord.Embed(title="Eine Katze!", color=0x7289DA)
            embed.set_image(url=response[0]["url"])
            await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
