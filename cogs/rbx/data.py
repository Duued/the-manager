
import base64
import hashlib
import json
import os
from typing import Any

import aiohttp
from discord.ext import commands


universeId = 4398944483
startUrl = f"https://apis.roblox.com/datastores/v1/universes/{universeId}/standard-datastores/"
headers = {"x-api-key": os.getenv('ROBLOX_API_KEY')}


def converttoMd5(data):
    return base64.b64encode(hashlib.md5(bytes(data)).digest()).decode()


async def write_to_key(datastore: str, key: str, data: Any):
    print(datastore)
    print(key)
    print(data)
    async with aiohttp.ClientSession() as session:
        data = json.dumps(data, separators=(",", ":")).encode()
        headers = {
            "x-api-key": os.getenv("ROBLOX_API_KEY"),
            "content-type": "application/json",
            "content-md5": converttoMd5(data),
        }
        async with session.post(
            f"{startUrl}datastore/entries/entry?datastoreName={datastore}&entryKey={key}", data=data, headers=headers
        ) as response:
            if response.status == 200:
                return 200
            else:
                r = await response.json()
                return r


async def fetch_key(datastore: str, key: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{startUrl}datastore/entries/entry?datastoreName={datastore}&entryKey={key}", headers=headers
        ) as response:
            r = await response.json()
            return r


class GameDataManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="game", invoke_without_command=True, ignore_extra=False)
    async def game(self, ctx: commands.Context):
        await ctx.send("This command is useless without any other command.")

    @game.command(name="ban", invoke_without_command=True, ignore_extra=False)
    @commands.is_owner()
    async def game_ban(self, ctx: commands.Context, user: int, *, reason="No reason provided."):
        code = await write_to_key("ModStore", f"Player_{user}", {"banned": True, "reason": reason})
        if code == 200:
            await ctx.send(f"User {user} has successfully been banned.")
        else:
            await ctx.send(code)

    @game.command(name="unban", invoke_without_command=True, ignore_extra=False)
    @commands.is_owner()
    async def game_unban(self, ctx: commands.Context, user: int):
        code = await write_to_key("ModStore", f"Player_{user}", {"autobanned": False, "banned": False, "reason": None})
        if code == 200:
            await ctx.send(f"User {user} has successfully been unbanned.")
        else:
            await ctx.send(code)

    @game.group(name="data", invoke_without_command=True, ignore_extra=False)
    @commands.is_owner()
    async def game_data(self, ctx: commands.Context, datastore: str, key: str, *, data):
        code = await write_to_key(datastore, key, data)
        if code == 200:
            await ctx.send(f"{data} written.")
        else:
            await ctx.send(code)

    @game_data.command(name="get")
    @commands.is_owner()
    async def get_game_data(self, ctx: commands.Context, datastore: str, key: str):
        code = await fetch_key(datastore, key)
        await ctx.send(code)


async def setup(bot):
    await bot.add_cog(GameDataManager(bot))
