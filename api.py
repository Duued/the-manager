import io
import os

import aiohttp
import discord

import errors


async def fetch(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Authorization": f"Bearer {os.getenv('PEXELS_API_KEY')}"}, params=params
        ) as response:
            if response.status != 200:
                raise errors.ApiError(await response.text())
            buf = io.BytesIO(await response.read())
            # r = await response.text()
            # return r
            return discord.File(buf, filename="image.png")
