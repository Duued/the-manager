import discord
from discord import app_commands
from discord.ext import commands


guildid = 867818989584777217


def is_forum():
    def predicate(interaction: discord.Interaction):
        return isinstance(interaction.channel, discord.Thread) and interaction.guild.id == guildid

    return app_commands.check(predicate)


def msgcanCloseTicket():
    def predicate(interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            raise app_commands.CheckFailure("This command must be ran in a thread.")
        channel: discord.Thread = interaction.channel
        if channel.owner == interaction.user:
            return True
        else:
            if channel.permissions_for(interaction.user).manage_threads:
                return True
        raise app_commands.CheckFailure("You do not have permission to close this thread.")

    return app_commands.check(predicate)


class LoveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="close", description="Closes a thread")
    @is_forum()
    @msgcanCloseTicket()
    async def close_thread(self, interaction: discord.Interaction):
        await interaction.response.send_message("This thread has been closed.")
        await interaction.channel.edit(locked=True, archived=True, reason=f"Closed by {interaction.user}")


async def setup(bot):
    await bot.add_cog(LoveCog(bot), guilds=[discord.Object(id=guildid)])
