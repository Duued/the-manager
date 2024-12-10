import asyncio
import io

import discord
import pytesseract
from discord import app_commands
from discord.ext import commands
from PIL import Image


class Ocr(commands.Cog):
    """Commands to read text from an image"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ocr")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.default, wait=True)
    @app_commands.describe(attachment="The attachment to read text from. Must be an image.")
    async def ocr_image(self, ctx: commands.Context, attachment: discord.Attachment | None = None):
        """Read text from an image"""
        async with ctx.typing():
            if attachment:
                fp = io.BytesIO()
                await attachment.save(fp)
                image = Image.open(fp)
                result: str | None = await asyncio.to_thread(pytesseract.image_to_string, image, timeout=120)
                result = result.strip()
                if result and result != "":
                    msg = f"Text: `{result}`"
                else:
                    msg = "No text detected."
                await ctx.send(msg)
            elif not attachment and ctx.message.reference is not None:
                message = ctx.message.reference.resolved
                try:
                    attachment = message.attachments[0]
                except IndexError:
                    return await ctx.reply("No attachment found.")
                if attachment.content_type.split("/")[0] == "image":
                    fp = io.BytesIO()
                    await attachment.save(fp)
                    image = Image.open(fp)
                    result: str | None = await asyncio.to_thread(pytesseract.image_to_string, image, timeout=120)
                    result = result.strip()
                    if result and result != "":
                        msg = f"Text: `{result}`"
                    else:
                        msg = "No text detected."
                    await ctx.send(msg)
                else:
                    return await ctx.reply("The attachment is not an image.")
            else:
                await ctx.send("Expected to be a reply, or have an attachment. Got None")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ocr(bot))
