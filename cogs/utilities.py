import typing

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands


class hexColorModal(ui.Modal, title="Enter your hex color code"):
    hex = ui.TextInput(
        label="Hex Color Code (do not include '0x' prefix)", placeholder="Hex Color Code", min_length=6, max_length=6
    )

    async def on_submit(self, interaction: discord.Interaction):
        color: discord.Color = discord.Color.from_str(f"#{self.hex.value}")
        embed = discord.Embed(title="Color", color=color)
        embed.add_field(name="Values", value=f"Hex: {hex(color.value)}\nRGB: {color.to_rgb()}\nDecimal: {color.value}")
        await interaction.response.send_message(embed=embed, view=None)


class rgbColorModal(ui.Modal, title="Enter the RGB color values"):
    r = ui.TextInput(label="Enter red", placeholder="Red - Color Code", min_length=0, max_length=3)
    g = ui.TextInput(label="Enter green", placeholder="Green - Color Code", min_length=0, max_length=3)
    b = ui.TextInput(label="Enter blue", placeholder="Blue - Color Code", min_length=0, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        if int(self.r.value) > 255:
            r = 0
        else:
            r = int(self.r.value) or 0
        if int(self.g.value) > 255:
            g = 0
        else:
            g = int(self.g.value) or 0
        if int(self.b.value) > 255:
            b = 0
        else:
            b = int(self.b.value) or 0

        color: discord.Color = discord.Color.from_rgb(r, g, b)
        embed = discord.Embed(title="Color", color=color)
        embed.add_field(name="Values", value=f"Hex: {color}\nRGB: {color.to_rgb()}\nDecimal: {color.value}")
        await interaction.response.send_message(embed=embed)


class DecimalColorModal(ui.Modal, title="Enter the Color Number Value"):
    number = ui.TextInput(label="Number", placeholder="Enter the number", max_length=7)

    async def on_submit(self, interaction: discord.Interaction):
        color: discord.Color = discord.Color.from_str(f"0x{hex(int(self.number.value))}")
        embed = discord.Embed(title="Color", color=color)
        embed.add_field(name="Values", value=f"Hex: {color}\nRGB: {color.to_rgb()}\nDecimal: {color.value}")
        await interaction.response.send_message(embed=embed)


class ColorInMethodPicker(ui.Select):
    def __init__(self, original_author: discord.User):
        self.original_author = original_author
        options = [
            discord.SelectOption(label="Hex", value="hex", description="Use a hexidecimal 0xffffff"),
            discord.SelectOption(label="RGB", value="rgb", description="Use a RGB value (255,255,255)"),
            discord.SelectOption(label="Decimal", value="int", description="Use a number 1245678"),
        ]
        super().__init__(placeholder="Pick your color input method.", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not your prompt.", ephemeral=True)
        if self.values[0] == "hex":
            await interaction.response.send_modal(hexColorModal())
        elif self.values[0] == "rgb":
            await interaction.response.send_modal(rgbColorModal())
        else:
            await interaction.response.send_modal(DecimalColorModal())


class ColorInMethodPickerView(ui.View):
    def __init__(self, original_author: discord.User):
        super().__init__(timeout=120)
        self.add_item(ColorInMethodPicker(original_author=original_author))


class ViewAvatar(ui.Select):
    def __init__(self, original_author: discord.User, viewing: typing.Union[discord.Member, discord.User]):
        self.original_author = original_author
        self.viewing = viewing
        options = [
            discord.SelectOption(
                label="Default Avatar",
                value="default",
                description=f"View {viewing.name}'s default avatar.",
                emoji="\U0001f195",
            ),
            discord.SelectOption(
                label="Display Avatar",
                value="display",
                description=f"View {viewing.name}'s display avatar.",
                emoji="\U0001f4f7",
            ),
            discord.SelectOption(
                label="Guild Avatar",
                value="guild",
                description=f"View {viewing.name}'s server avatar, or display if there is none.",
                emoji="\U0001f3de",
            ),
            discord.SelectOption(
                label="Close Menu",
                value="close",
                description=f"Close this menu while keeping the message.",
                emoji="\U0000274c",
            ),
            discord.SelectOption(
                label="Delete Message", value="delete", description=f"Delete this message.", emoji="\U0001f5d1"
            ),
        ]
        super().__init__(min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.original_author:
            await interaction.response.send_message("This is not your prompt.", ephemeral=True)
        else:
            avatar = None
            if self.values[0] == "delete":
                await interaction.message.delete()
                return
            elif self.values[0] == "close":
                await interaction.message.edit(content="Closed by user.", view=None)
            elif self.values[0] == "default":
                avatar = self.viewing.default_avatar
            elif self.values[0] == "display":
                avatar = self.viewing.display_avatar
            elif self.values[0] == "guild":
                avatar = self.viewing.guild_avatar or self.viewing.display_avatar
            text = self.values[0] or "display"
            embed = discord.Embed(title=f"{self.viewing.name}'s {text} avatar", color=0x7289DA)
            embed.set_image(url=avatar.url)
            await interaction.response.edit_message(embed=embed)


class ViewAvatarView(ui.View):
    def __init__(self, original_author: discord.User, viewing: discord.User):
        super().__init__()
        self.add_item(ViewAvatar(original_author=original_author, viewing=viewing))

    async def on_timeout(self):
        await self.message.edit(content="Timed out! Run again to continue.", view=None)


class Utilities(commands.Cog, name="utilities"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="color", description="Gets a color and gives information on it")
    async def color(self, interaction: discord.Interaction):
        view = ColorInMethodPickerView(interaction.user)
        await interaction.response.defer(ephemeral=False, thinking=False)
        await interaction.edit_original_response(content="How would you like to input the color?", view=view)

    @app_commands.command(name="avatar", description="Get a user avatar. Leave user empty for your own.")
    @app_commands.describe(user="The user avatar. Leave empty for your own")
    async def view_user_avatar(
        self, interaction: discord.Interaction, user: typing.Union[discord.Member, discord.User] = None
    ):
        user = user or interaction.user
        await interaction.response.defer()
        view = ViewAvatarView(interaction.user, user)
        await interaction.edit_original_response(
            content=f"Pick which of {user.mention}'s avatars to view",
            view=view,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        view.message = interaction.original_response()

    @app_commands.command(name="ping", description="Get the bot latency.")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="The Manager - Ping",
            description=f"Calculated round-trip time: {round(self.bot.latency*1000)}ms",
            color=0x7289DA,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete-webhook", description="Delete a webhook.")
    @app_commands.describe(url="The target webhook URL.")
    async def delete_webhook(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                await interaction.edit_original_response(content="The webhook was deleted.")

    @app_commands.command(name="invite", description="Invite a bot")
    @app_commands.describe(bot="The bot user to invite. Leave empty for this bot.")
    async def invite_bot(self, interaction: discord.Interaction, bot: discord.User = None):
        if bot and not bot.bot:
            await interaction.response.send_message("This user is not a bot", ephemeral=True)
        elif bot and bot.id == 80528701850124288:
            await interaction.response.send_message(
                "https://discord.com/oauth2/authorize?client_id=169293305274826754&scope=bot+applications.commands&permissions=268823638",
                ephemeral=True,
            )
        elif bot and bot == interaction.client:
            await interaction.response.send_message(interaction.client.application.custom_install_url)
        elif bot:
            await interaction.response.send_message(discord.utils.oauth_url(bot.id), ephemeral=True)
        else:
            return await interaction.response.send_message(interaction.client.application.custom_install_url, ephemeral=True)

    # @app_commands.command(name="define", description="Define a word in the English dictionary")
    # @app_commands.describe(word="The word to search for")
    # async def define_word(self, interaction: discord.Interaction, word: str):
    #    await interaction.response.defer()
    #    async with aiohttp.ClientSession() as session:
    #        url = yarl.url("https://www.thefreedictionary.com") / word
    #
    #        async with session.get(url) as resp:
    #            if resp.status != 200:
    #                await interaction.edit_original_response(content="An error has occured. Please try again.")
    #        text = await resp.text()
    #        document = html.document_fromstring(text)
    #
    #        try:
    #            definitions = document.get_element_by_id('Definition')
    #        except KeyError:


async def setup(bot):
    await bot.add_cog(Utilities(bot))
