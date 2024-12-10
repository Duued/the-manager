import os

import aiohttp
import discord
import dotenv
from discord import app_commands
from discord.ext import commands


dotenv.load_dotenv(verbose=True)

Authorization = os.getenv("GITHUB_API_KEY")
base_url = "https://api.github.com/"


async def create_pull_request(title, body, owner: str, repo: str, head, base):
    headers = {"Authorization": f"Bearer {Authorization}"}
    params = {"title": title, "body": body, "head": head, "base": base}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}{owner}{repo}", headers=headers, params=params) as response:
            if response.status != 200:
                return {"status": response.status, "text": await response.text()}
            else:
                return "Done!"
