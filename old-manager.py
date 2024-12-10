import datetime
import logging
import os
import traceback

import discord
import dotenv
from discord import app_commands, ui
from discord.ext import commands
from discord.ui import view


# from pymongo_get_database import get_database

# db = get_database()

extensions = [
    "jishaku",
    "cogs.utilities",
    "cogs.channels",
    "cogs.dev",
    "cogs.fun",
    "cogs.image_manipulation",
    "cogs.calculator",
    "cogs.anonymous",
    "cogs.love",
]
skip = []

allow = "<:Allow:1015412118826274907>"
deny = "<:Deny:1015411666453807136>"

dotenv.load_dotenv(verbose=True)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

    async def setup_hook(self):
        for extension in extensions:
            if not extension in skip:
                try:
                    await bot.load_extension(extension)
                except Exception as e:
                    print(e)
                    continue


class Tree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, exception: app_commands.AppCommandError):
        tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
        if interaction.command:
            print(f"Error running command {interaction.command.name} by user {interaction.user}")
        print(exception)
        print("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

        msg = ""
        allowedView = True

        if isinstance(exception, app_commands.NoPrivateMessage):
            msg = "This message cannot be ran in DMs."
            allowedView = False
        elif isinstance(exception, app_commands.BotMissingPermissions):
            msg = "The bot lacks the sufficient permissions to run this command."
            allowedView = False
        elif isinstance(exception, app_commands.MissingPermissions):
            msg = "You lack the sufficient permissions to run this command."
            allowedView = False
        elif isinstance(exception, app_commands.CheckFailure):
            msg = exception
            allowedView = False
        msg = msg or exception
        if allowedView:
            view = GetTraceback(exception)
        else:
            view = None
        if interaction.response.is_done():
            await interaction.edit_original_response(content=f"Error: {msg}", view=view)
        else:
            await interaction.response.send_message(content=f"Error: {msg}", view=view)

    async def interaction_check(self, interaction: discord.Interaction):
        if bot.locked:
            if await interaction.client.is_owner(interaction.user) or interaction.user.id == 986757153979260928:
                return True
            else:
                raise app_commands.CheckFailure(f"{deny} The bot is currently disabled.")

        # data =  db[f'userstatus-{interaction.user.id}']
        # if data['botban'] == True:
        #    raise app_commands.CheckFailure("You're banned from using the bot.")

        return True


class GetTraceback(ui.View):
    def __init__(self, exception):
        super().__init__(timeout=600)
        self.exception = exception

    def on_timeout(self):
        for item in self.children:
            item.disabled = True

    @ui.button(label="Get traceback", style=discord.ButtonStyle.primary)
    async def get_traceback(self, interaction: discord.Interaction, button: discord.Button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=None)
        await interaction.response.defer(ephemeral=False, thinking=False)
        tb = traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__)
        text = "".join(tb)
        p = commands.Paginator(prefix="```py", suffix="```")
        for line in text.splitlines():
            p.add_line(line)
        for page in p.pages:
            await interaction.followup.send(page)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

bot = Bot(
    command_prefix=commands.when_mentioned_or("*"),
    strip_after_prefix=True,
    case_insensitive=True,
    intents=intents,
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.watching, name="karens."),
    tree_cls=Tree,
)

bot.locked = False


@bot.event
async def on_command_error(ctx: commands.Context, exception):
    if not isinstance(exception, commands.CommandNotFound):
        await ctx.reply(exception, allowed_mentions=discord.AllowedMentions.none())


@bot.check
async def lock_check(ctx):
    if bot.locked:
        if await ctx.bot.is_owner(ctx.author) or ctx.author.id == 986757153979260928:
            return True
        raise commands.CheckFailure("The bot is currently disabled.")
    else:
        return True


bot.run(os.getenv("TOKEN"), log_handler=handler, log_level=logging.ERROR)
