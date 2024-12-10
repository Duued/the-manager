import discord
from discord import app_commands
from discord.ext import commands


devserver = 1120505743913791528


def is_admin():
    def predicate(ctx: commands.Context):
        if not ctx.guild or ctx.guild.id != 1120505743913791528:
            raise commands.CheckFailure("Must be ran in DogKnife Development")
        if ctx.author.guild_permissions.administrator:
            return True
        roles = ["Head Administrator", "Administrator", "admin perms", "*"]
        if any(
            ctx.author.get_role(item) is not None
            if isinstance(item, int)
            else discord.utils.get(ctx.author.roles, name=item) is not None
            for item in roles
        ):
            return True
        raise commands.MissingAnyRole(list(roles))

    return commands.check(predicate)


class DevelopmentServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == 1129521321089449985:
            if not message.guild.get_role(1131414043568115793) in message.author.roles:
                await message.author.add_roles(
                    discord.Object(id=1131414043568115793), reason="Member sent their first introduction."
                )

    @commands.command(
        name="bypass-guild-verification",
        aliases=["verify"],
        brief="Allows a user to bypass discord's verification requirements.",
    )
    @is_admin()
    async def bypass_user_verification(self, ctx: commands.Context, member: discord.Member):
        await member.edit(bypass_verification=True, reason=f"{ctx.author} requested bypass for member.")

    # @app_commands.command(name="roulette")


async def setup(bot):
    await bot.add_cog(DevelopmentServer(bot))
