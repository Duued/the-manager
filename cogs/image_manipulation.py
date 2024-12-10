import io
import os
import typing

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv(verbose=True)
base_url = "https://api.jeyy.xyz/v2"
pexels_base_url = "https://api.pexels.com/v1/"


async def fetch(session, url, params):
    async with session.get(url, headers={"Authorization": f"Bearer {os.getenv('JEYY_API_KEY')}"}, params=params) as response:
        buf = io.BytesIO(await response.read())
        # r = await response.text()
        # return r
        return discord.File(buf, filename="image.gif")


class Images(commands.GroupCog, name="images"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="abstract", description="Generate an abstract gif of a image, avatar, or url. Leave all empty for your avatar."
    )
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_abstract(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "abstract"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            print(f"THE URL IS {url}")
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        # await interaction.edit_original_response(content=response)
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="ads", description="Create an advertisement for an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_ad(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "ads"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="balls", description="Generate a fancy ball effect for an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_balls(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "balls"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="bayer", description="Generate a DigiSign effect.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_bayer(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "bayer"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="billboard", description="Put an image on a billboard.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_billboard(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "billboard"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="blocks", description="Generate a block effect for an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_blocks(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "blocks"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="blur", description="Blurs an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_blur(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "blur"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="boil", description="Generate a boiling water effect for an image.")
    @app_commands.describe(
        user="The user avatar to use",
        attachment="An attachment to use.",
        url="An image url to use",
        level="The boil intensity",
    )
    async def generate_boil_effect(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
        level: int = 2,
    ):
        thiscmd = "boil"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url, "level": level})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url, "level": level})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url, "level": level})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url, "level": level})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="bomb", description="Blow up an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_bomb(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "bomb"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="bonk", description="Bonk an image with a newspaper.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_bonk(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "bonks"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="bubble", description="Gives an image a bubble fade-in effect.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_bubble(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "bubble"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="burn", description="Commit arson on an image")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_burn(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "burn"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="cartoon", description="Turn an image into a cartoonized image")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_cartoon(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "cartoon"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="cinema", description="Watch a cartoon on the cinema big screen.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_cinema(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "cinema"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="clock", description="Turn an image into a clock.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_clock(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "clock"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="cow", description="Turn an image into a cow.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_cow(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "cow"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="cracks", description="OH MY GOD! WHO USED POSTERIZE INCORRECTLY? Oh wait, it's just an API.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_cracks(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "cracks"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="cube", description="Turn an image into a cube.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def generate_cube(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "cube"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])

    @app_commands.command(name="dilate", description="Dilate an image.")
    @app_commands.describe(user="The user avatar to use", attachment="An attachment to use.", url="An image url to use")
    async def dialate_image(
        self,
        interaction: discord.Interaction,
        user: typing.Union[discord.Member, discord.User] = None,
        attachment: discord.Attachment = None,
        url: str = None,
    ):
        thiscmd = "dilate"
        await interaction.response.defer(thinking=True)
        response = None
        if user is None and attachment == user and url == user:
            url = interaction.user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif user:
            url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        elif url:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        else:
            url = attachment.url
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, url=f"{base_url}/image/{thiscmd}", params={"image_url": url})
        await interaction.edit_original_response(attachments=[response])


async def setup(bot):
    await bot.add_cog(Images(bot))
