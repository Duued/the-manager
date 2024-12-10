import os
import secrets
import typing

import discord
import dotenv
import mystbin
from discord.ext import commands


dotenv.load_dotenv(verbose=True)


class GuildListFlags(commands.FlagConverter, case_insensitive=True, prefix="-", delimiter=" "):
    password: typing.Union[bool, str] = True
    bytes: int = 16
    delete_after: int | None = None


class GuildManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.mb_client = mystbin.Client(token=os.getenv("MYSTBIN_API_KEY"))

    async def cog_check(self, ctx: commands.Context):
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.CheckFailure(f"You must own this bot to use {ctx.command.qualified_name}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        banned = await self.bot.db.fetchval("SELECT banned FROM guildmanager WHERE id=$1", (guild.id))
        if banned:
            systemchannel = guild.system_channel

            if systemchannel:
                try:
                    await systemchannel.send("The bot is banned from this guild.")
                except AttributeError:
                    pass
            await guild.leave()

    @commands.command(name="guildban", aliases=["guban"], brief="Bans a guild from using the bot.")
    async def do_guildban(self, ctx: commands.Context, guild: typing.Union[int, discord.Guild]):
        async with ctx.typing():
            id = 0
            if isinstance(guild, discord.Guild):
                id = guild.id
            else:
                id = guild
            await ctx.bot.db.execute(
                """INSERT INTO guildmanager(id, banned)
                                    
                                    VALUES($1, True)""",
                (id),
            )
            await ctx.reply(f"{id} has been banned", mention_author=True)
            g: discord.Guild | None = ctx.bot.get_guild(id)
            if g:
                systemchannel: discord.TextChannel | None = g.system_channel
                if systemchannel:
                    try:
                        await systemchannel.send("Bot has been banned from this guild...\nLeaving")
                    except AttributeError:
                        pass
                await g.leave()

    @commands.command(name="unguildban", aliases=["unguban"], brief="The exact opposite of guildban")
    async def unguildban(self, ctx: commands.Context, guild: typing.Union[int, discord.Guild]):
        async with ctx.typing():
            id = 0
            if isinstance(guild, discord.Guild):
                id = guild.id
            else:
                id = guild
            await ctx.bot.db.execute("DELETE FROM guildmanager WHERE id=$1", (id))
            await ctx.reply(f"Unbanned {id}")

    @commands.command(name="list")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def list_all_guilds(self, ctx: commands.Context, *, flags: GuildListFlags):
        """Dumps all guild information into a mystbin link.

        Flags allows you to set delete_after and file password

        Args:
            flags: Allows you to set `-password`, `-bytes` and`-delete_after`

        Examples:
        [prefix] list -password [bool | str]
        [prefix] list -password True -bytes [int] # Bytes only works if password is true
        [prefix] list -delete_after [int] # Seconds to wait before deleting message
        """
        async with ctx.typing():
            guild: discord.Guild
            text = ""
            for guild in ctx.bot.guilds:
                text += f"Guild: {guild.name} ({guild.id}), Owner: {guild.owner} ({guild.owner_id}) Members: {guild.member_count}\n"
            if isinstance(flags.password, bool):
                if flags.password is True:
                    password = secrets.token_urlsafe(flags.bytes)
                else:
                    password = None
            else:
                password = flags.password

            paste: mystbin.paste = await self.mb_client.create_paste(
                filename="guild-list.txt", content=text, password=password
            )

        message: discord.Message = await ctx.send(paste, delete_after=flags.delete_after)
        if password is not False and password is not None:
            await ctx.author.send(f"{message.jump_url} - {password}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildManager(bot))
