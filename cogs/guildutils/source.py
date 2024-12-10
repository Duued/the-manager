import datetime
import json
import os

import discord
import mystbin
from discord import app_commands
from discord.ext import commands

from cogs import beta


class Source(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_ctx_menu = app_commands.ContextMenu(name="Message Information", callback=self.message_info)
        self.mb_client = mystbin.Client(token=os.getenv("MYSTBIN_API_KEY"))
        self.bot.tree.add_command(self.message_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.message_ctx_menu.name, type=self.message_ctx_menu.type)

    @beta.is_beta_i()
    async def message_info(self, interaction: discord.Interaction, message: discord.Message):
        embed = discord.Embed(
            title="Message Information",
            description="Parts of the message that aren't so easy to get will be displayed here.\n\nWorking... Please wait",
            color=0x7289DA,
            timestamp=datetime.datetime.now(),
        )
        await interaction.response.send_message(embed=embed)
        embed.description = ""
        raw_content = ""
        if message.content:
            raw_content = f"Raw Content: {discord.utils.escape_markdown(message.clean_content, as_needed=True)}\n"
        embed.description += raw_content
        paste = None
        content = ""
        if len(message.embeds) >= 1:
            content = ""
            for e in message.embeds:
                content += f"{json.dumps(e.to_dict())}\n"
            if len(content) > 1975:
                paste = await self.mb_client.create_paste(filename="embedcontent.json", content=content)
        if paste:
            embed.description += f"{paste}\n"
        elif content and not paste:
            embed.description += f"Embed JSON: ```json\n{content}\n```"
        embed.timestamp = datetime.datetime.now()
        await interaction.edit_original_response(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Source(bot))
