import asyncio
import datetime
import logging
import os
import traceback

import asyncpg
import discord
import dotenv
from discord import app_commands, ui
from discord.ext import commands

import advancedlogging


LOGGER = logging.getLogger(__name__)

extensions = [
    "cogs.logging",
    "cogs.guildmanager",
    "cogs.smartthings",
    "jishaku",
    "cogs.utilities",
    "cogs.guild.channels",
    "cogs.dev",
    "cogs.sql",
    "cogs.fun",
    "cogs.image_manipulation",
    "cogs.calculator",
    "cogs.anonymous",
    "cogs.love",
    "cogs.dssp.report",
    "cogs.general",
    "cogs.devserver.main",
    "cogs.devserver.tickets",
    "cogs.devserver.forums",
    "cogs.embed",
    "cogs.info",
    "cogs.botlogging",
    "cogs.mystbin",
    "cogs.beta",
    "cogs.globaltags",
    "cogs.moderation",
    "cogs.macrodroid",
    "cogs.guildutils.source",
    "cogs.economy",
    "cogs.reminders",
    "cogs.gbans",
    "cogs.guildutils.member-manager",
    "cogs.phone",
    "cogs.thriller.antiping",
    "cogs.thriller.autoban"
]
skip = []

allow = "<:Allow:1015412118826274907>"
deny = "<:Deny:1015411666453807136>"

dotenv.load_dotenv(verbose=True)

credentials = {"user": "dogs", "password": os.getenv("dbpass"), "database": "manager", "host": "127.0.0.1"}


async def getprefix(bot: commands.Bot, message: discord.Message):
    prefixes = ["*", "mgr", "manager", bot.user.mention]
    if message.guild is None or message.channel.id == 1129541396089536643:  # The Manager Channel in DogKnife Development
        prefixes.append("")
    if (
        message.guild
        and isinstance(message.channel, discord.TextChannel)
        and message.channel.topic is not None
        and "--the-manager-prefixless" in message.channel.topic.lower()
    ):
        prefixes.append("")
    return prefixes


class Bot(commands.Bot):
    db: asyncpg.pool.Pool | None

    def __init__(self, *args, **kwargs):
        self.logging_queue = asyncio.Queue()
        self.handler = advancedlogging.LogHandler(bot=self)
        self.errorhandler_enabled = True
        super().__init__(*args, **kwargs)

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

    async def setup_hook(self):
        self.db: asyncpg.pool.Pool = await asyncpg.create_pool(**credentials)
        for extension in extensions:
            if extension not in skip:
                try:
                    await bot.load_extension(extension)
                    LOGGER.info(msg=f"Loaded extension {extension}")
                except Exception as e:
                    print(e)
                    LOGGER.error(msg=f"Error loading {extension}\n\n{e}")
                    continue

    async def close(self):
        await self.session.close()
        await self.db.close()
        await super().close()


view_disabled_exceptions: list[Exception] = [
    app_commands.NoPrivateMessage,
    app_commands.BotMissingPermissions,
    app_commands.MissingPermissions,
    app_commands.CheckFailure,
    commands.UserInputError,
    commands.CheckFailure,
]


class Tree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, exception: app_commands.AppCommandError):
        if interaction.command:
            print(f"Error running command {interaction.command.name} by user {interaction.user}")
        print(exception)
        print("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

        msg = ""
        allowedView = True

        for disabled_exception in view_disabled_exceptions:
            if isinstance(exception, disabled_exception):
                allowedView = False
        msg = msg or exception
        if allowedView:
            view = GetTraceback(exception)
        else:
            view = None
        embed = discord.Embed(
            title="An error has occured", description=msg, color=discord.Color.red(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
        embed.set_footer(text="Dog Knife's The Manager")
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    async def interaction_check(self, interaction: discord.Interaction):
        if bot.locked:
            if await interaction.client.is_owner(interaction.user) or interaction.user.id == 986757153979260928:
                return True
            else:
                raise app_commands.CheckFailure(":x: The bot is currently disabled.")

        banned = await bot.db.fetchrow("SELECT banned FROM users WHERE id=$1", (interaction.user.id))
        if banned:
            raise app_commands.CheckFailure(":x: You are banned from using this bot.")
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
    command_prefix=getprefix,
    strip_after_prefix=True,
    case_insensitive=True,
    intents=intents,
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.watching, name="karens."),
    tree_cls=Tree,
)

bot.locked = False

bot.owner_id = None
bot.owner_ids = [561565119201673216, 986757153979260928]


@bot.event
async def on_command_error(ctx: commands.Context, exception, *args):
    msg = ""
    allowedView = True

    for disabled_exception in view_disabled_exceptions:
        if isinstance(exception, disabled_exception):
            allowedView = False

    if isinstance(exception, commands.CommandNotFound):
        return
    else:
        view = GetTraceback(exception)
        await ctx.send(msg or exception, allowed_mentions=discord.AllowedMentions.none(), view=view if allowedView else None)


@bot.check
async def lock_check(ctx):
    if bot.locked:
        if await ctx.bot.is_owner(ctx.author) or ctx.author.id == 986757153979260928:
            return True
        raise commands.CheckFailure("The bot is currently disabled.")
    else:
        banned = await bot.db.fetchrow("SELECT banned FROM users WHERE id=$1", (ctx.author.id))
        if banned:
            raise commands.CheckFailure("You are banned from using this bot.")
        return True


bot.run(os.getenv("TOKEN"), log_handler=handler, log_level=logging.ERROR)
