import os

import discord
import dotenv
import mystbin
from discord import app_commands, ui
from discord.ext import commands


dotenv.load_dotenv(verbose=True)


class FileModal(ui.Modal, title="File Input Form"):
    def __init__(self, mb_client: mystbin.client):
        self.mb_client: mystbin.client = mb_client
        super().__init__()

    filename = ui.TextInput(label="File name", placeholder="Enter the file name with an optional extension.")
    text = ui.TextInput(label="Enter your text", style=discord.TextStyle.paragraph, placeholder="Enter your content text.")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        paste = await self.mb_client.create_paste(filename=self.filename.value, content=self.text.value)
        await interaction.delete_original_response()
        await interaction.followup.send(content=paste, ephemeral=True)


class Mystbin(commands.GroupCog, name="paste"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mb_client = mystbin.Client(token=os.getenv("MYSTBIN_API_KEY"))

    @app_commands.command(name="create", description="Create a paste using mystb.in")
    @app_commands.describe(file="The file to use. Leave empty to paste code into a prompt.")
    async def create_mystbin_file(self, interaction: discord.Interaction, file: discord.Attachment = None):
        if file:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(content="Please wait. This may take some time...")
            byts = await file.read()
            content = byts.decode()
            file = mystbin.File(filename=file.filename, content=content, attachment_url=None)
            paste = await self.mb_client.create_paste(file=file)
            await interaction.delete_original_response()
            await interaction.followup.send(content=paste, ephemeral=True)
        else:
            await interaction.response.send_modal(FileModal(self.mb_client))


async def setup(bot):
    await bot.add_cog(Mystbin(bot))
