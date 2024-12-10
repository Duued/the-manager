import datetime

import discord
from discord import app_commands, ui
from discord.ext import commands
from discord.ui import view

import github


class ReportSiteModal(ui.Modal, title="Site report"):
    website = ui.TextInput(
        label="Website URL", style=discord.TextStyle.short, placeholder="Do not include https", min_length=1, max_length=256
    )
    reason = ui.TextInput(
        label="What about this site is malicious?",
        style=discord.TextStyle.paragraph,
        placeholder="Explain how this site is malicious",
        min_length=50,
        max_length=256,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await interaction.client.db.fetchval("SELECT destination FROM reports")
        channel = interaction.client.get_channel(channel)
        embed = discord.Embed(
            title="Website Report",
            description="A user has submitted a website report!",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar)
        embed.set_footer(text="Bot created by dogknife.")
        embed.add_field(name="Website", value=self.website.value, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=True)

        entries = len(await interaction.client.db.fetch("SELECT * FROM report"))

        await interaction.client.db.execute(
            """
        INSERT INTO report(author, url, reason, id)                                            
        VALUES($1, $2, $3, $4)             """,
            interaction.user.id,
            self.website.value,
            self.reason.value,
            entries,
        )
        message = await channel.send(embed=embed)
        thread = await message.create_thread(
            name=f"report #{entries}-{interaction.user.name}",
            auto_archive_duration=10080,
            reason="Creating followup thread.",
        )
        await thread.send(
            f"Hello {interaction.user.mention}. Thank you for reporting this site! This thread will be used for follow-up messaging and updates!"
        )
        await interaction.edit_original_response(content=f"Sent to administration. Check {thread.mention} for updates!")


class Report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="report", description="Report a scam website.")
    async def report_suspicious_website(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportSiteModal())

    @app_commands.command(name="add", description="Creates PR to put the URL into GitHub")
    @app_commands.describe(url="The url to PR. Omit http/https")
    async def add_url_to_git(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        response = await github.create_pull_request(
            title=f"New URL reported by Discord User {interaction.user.name} ({interaction.user.id})",
            body=url,
            owner="Discord-AntiScam",
            repo="scam-links",
            head=f"duued:url-discord-user{interaction.user.id}",
            base="master",
        )
        await interaction.edit_original_response(content=response)


async def setup(bot):
    await bot.add_cog(Report(bot), guilds=[discord.Object(id=923158511968464898)])
