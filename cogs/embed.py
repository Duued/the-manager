import json
import os
import typing
from typing import Union

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands

import errors


async def write_file(name: str, content: dict):
    file = open(f"./temp/embeds/{name}.json", "w+")
    file.write(json.dumps(content))
    file.close()
    file = open(f"./temp/embeds/{name}.json", "r")
    return file


def to_bool(input: typing.Union[str, bool]) -> bool:
    if isinstance(input, str):
        lowered = input.lower()
        if lowered in ("yes", "y", "true", "t", "1", "on"):
            return True
        elif lowered in ("no", "n", "false", "f", "0", "off"):
            return False
        else:
            raise errors.InvalidTypeException(f"Expected yes/no, true/false, got {input}")
    else:
        return input


class SelectFieldToEditView(ui.View):
    def __init__(self, original_author: discord.User, embed: discord.Embed):
        super().__init__()
        self.original_author = original_author
        self.embed = embed
        index = 0
        for field in embed.fields:
            self.field_select.add_option(label=field.name, value=index)
            index += 1

    @ui.select(max_values=1, min_values=1, placeholder="Select a field to edit")
    async def field_select(self, interaction: discord.Interaction, select: ui.Select):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not for you.")
        await interaction.response.send_modal(UpdateExistingFieldModal2(self.embed, int(select.values[0])))


class SelectFieldToDeleteView(ui.View):
    def __init__(self, original_author: discord.User, embed: discord.Embed):
        super().__init__()
        self.original_author = original_author
        self.embed = embed
        index = 0
        for field in embed.fields:
            self.field_select.add_option(label=field.name, value=index)
            index += 1

    @ui.select(max_values=1, min_values=1, placeholder="Select a field to delete")
    async def field_select(self, interaction: discord.Interaction, select: ui.Select):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not for you.")
        self.embed.remove_field(int(select.values[0]))
        if self.embed.title == "" and self.embed.description == "" and len(self.embed.fields) == 0:
            self.embed.description = (
                "Both title and description cannot be blank while there are no fields. (Discord limitation)"
            )
        await interaction.response.edit_message(embed=self.embed, view=EmbedEditView(interaction.user, self.embed))


class EmbedButton(ui.Button):
    def __init__(
        self,
        embed: discord.Embed,
        original_author: discord.User,
        label: str,
        style: discord.ButtonStyle,
        row: int,
        disabled: bool = False,
    ):
        self.embed = embed
        self.original_author = original_author
        super().__init__(label=label, style=style, row=row, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)
        if self.label == "Embed":
            await interaction.response.send_modal(MainEmbedUpdateModal(self.embed))
        elif self.label == "Author":
            await interaction.response.send_modal(AuthorUpdateModal(self.embed))
        elif self.label == "Footer":
            await interaction.response.send_modal(FooterUpdateModal(self.embed))
        elif self.label == "Image":
            await interaction.response.send_modal(ImageUpdateModal(self.embed))
        elif self.label == "+":
            await interaction.response.send_modal(AddFieldModal(self.embed))
        elif self.label == "-":
            if len(self.embed.fields) == 0:
                return await interaction.response.edit_message(content="No fields to delete. Try something else.")
            await interaction.response.edit_message(view=SelectFieldToDeleteView(interaction.user, self.embed))
        elif self.label == "Edit":
            if len(self.embed.fields) == 0:
                return await interaction.response.edit_message(content="No fields to edit. Try something else.")
            await interaction.response.edit_message(
                embed=self.embed, view=SelectFieldToEditView(interaction.user, self.embed)
            )
        elif self.label == "Send Here":
            msg = ""
            if interaction.channel.permissions_for(interaction.user).send_messages:
                await interaction.channel.send(embed=self.embed)
                msg = "Sent!"
            else:
                msg = "You do not have permission to send messages in this channel."
            await interaction.response.send_message(msg, ephemeral=True)
        elif self.label == "Send to Channel":
            await interaction.response.defer()
            view = SendView(interaction.user, self.embed)
            await interaction.edit_original_response(view=view)
            view.message = await interaction.original_response()
        elif self.label == "DM":
            try:
                await interaction.user.send(embed=self.embed)
            except discord.Forbidden:
                return await interaction.response.send_message("Open your DMs and try again!")
            await interaction.response.send_message("Sent!", ephemeral=True)
        elif self.label == "Save to bot":
            await interaction.response.send_modal(SaveToBotModal(self.embed))
        elif self.label == "Save to file":
            await write_file(interaction.user.id, self.embed.to_dict())
            await interaction.response.send_message(
                "Your file:", file=discord.File(f"./temp/embeds/{interaction.user.id}.json"), ephemeral=True
            )
            os.remove(f"./temp/embeds/{interaction.user.id}.json")
        elif self.label == "Send to Webhook":
            await interaction.response.send_modal(sendToWebhook(self.embed))


class EmbedEditView(ui.View):
    message: discord.Message | discord.WebhookMessage

    def __init__(self, original_author: discord.User, embed: discord.Embed):
        super().__init__(timeout=600)
        self.original_author = original_author
        self.embed = embed

        self.add_item(EmbedButton(embed, original_author, "Edit:", discord.ButtonStyle.gray, 0, True))
        self.add_item(EmbedButton(embed, original_author, "Embed", discord.ButtonStyle.blurple, 0))
        self.add_item(EmbedButton(embed, original_author, "Author", discord.ButtonStyle.blurple, 0))
        self.add_item(EmbedButton(embed, original_author, "Footer", discord.ButtonStyle.blurple, 0))
        self.add_item(EmbedButton(embed, original_author, "Image", discord.ButtonStyle.blurple, 0))
        # Row 1 - Embed Management (0 index)

        self.add_item(EmbedButton(embed, original_author, "Fields:", discord.ButtonStyle.gray, 1, True))
        self.add_item(EmbedButton(embed, original_author, "+", discord.ButtonStyle.success, 1))
        self.add_item(EmbedButton(embed, original_author, "-", discord.ButtonStyle.danger, 1))
        self.add_item(EmbedButton(embed, original_author, "Edit", discord.ButtonStyle.blurple, 1, False))
        # Row 2 - Field Management

        self.add_item(EmbedButton(embed, original_author, "Send:", discord.ButtonStyle.gray, 2, True))
        self.add_item(EmbedButton(embed, original_author, "Send Here", discord.ButtonStyle.success, 2))
        self.add_item(EmbedButton(embed, original_author, "Send to Channel", discord.ButtonStyle.success, 2))
        self.add_item(EmbedButton(embed, original_author, "Send to Webhook", discord.ButtonStyle.success, 2))
        self.add_item(EmbedButton(embed, original_author, "DM", discord.ButtonStyle.success, 2))
        # Row 3 - Sending Embed

        self.add_item(EmbedButton(embed, original_author, "Save:", discord.ButtonStyle.gray, 3, True))
        self.add_item(EmbedButton(embed, original_author, "Save to bot", discord.ButtonStyle.green, 3))
        self.add_item(EmbedButton(embed, original_author, "Save to file", discord.ButtonStyle.green, 3))
        # Row 4 - Saving Embed

    async def on_timeout(self):
        await self.message.edit(view=None)


class MainEmbedUpdateModal(ui.Modal, title="Main Embed Configuration"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.t.default = embed.title
        self.description.default = embed.description
        if self.embed.color is not None:
            self.color.default = hex(self.embed.color.value).replace("0x", "#")
        else:
            self.color.default = "#000000"
        super().__init__()

    t = ui.TextInput(
        label="Embed title",
        placeholder="Enter the embed title. This can only be up to 256 characters",
        max_length=256,
        required=False,
        style=discord.TextStyle.short,
    )
    description = ui.TextInput(label="description", max_length=4000, style=discord.TextStyle.paragraph, required=False)
    color = ui.TextInput(label="Color", placeholder="The color. Supports #xxxxxx and RGB", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.title = self.t.value
        self.embed.description = self.description.value
        try:
            self.embed.color = discord.Color.from_str(self.color.value) or None
        except Exception as e:
            print(e)
            pass
        if self.t.value == "" and self.description.value == "" and len(self.embed.fields) == 0:
            self.embed.title = ""
            self.embed.description = (
                "Both title and description cannot be blank while there are no fields. (Discord limitation)"
            )
        await interaction.edit_original_response(content="", embed=self.embed)


class AuthorUpdateModal(ui.Modal, title="Embed Author Information Editor"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.name = embed.author.name
        self.url = embed.author.url
        self.icon_url = embed.author.icon_url
        super().__init__()

    name = ui.TextInput(label="Author name", placeholder="Enter the name of the Author", required=False)
    url = ui.TextInput(
        label="Author URL",
        placeholder="Enter a URL for the author. This allows users to click on the author name to go to a website!",
        required=False,
    )
    icon_url = ui.TextInput(
        label="Author Icon URL", placeholder="Enter the icon URL of the author. Only HTTP(S) is supported!", required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.set_author(name=self.name.value, url=self.url.value, icon_url=self.icon_url.value)
        await interaction.edit_original_response(content="", embed=self.embed)


class FooterUpdateModal(ui.Modal, title="Embed Footer Information Editor"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.text.default = embed.footer.text
        self.icon_url.default = embed.footer.icon_url
        super().__init__()

    text = ui.TextInput(label="Footer Text", placeholder="Enter the footer text here", max_length=2048, required=False)
    icon_url = ui.TextInput(
        label="Footer Icon URL", placeholder="Enter the footer icon URL here. Onyl HTTP(S) is supported!", required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.set_footer(text=self.text.value, icon_url=self.icon_url.value)
        await interaction.edit_original_response(content="", embed=self.embed)


class ImageUpdateModal(ui.Modal, title="Embed Image Editor"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.url.default = embed.image.url
        super().__init__()

    url = ui.TextInput(label="Image URL", placeholder="Enter a image URL. Note only HTTP(S) is supported!", required=False)
    thumbnail = ui.TextInput(
        label="Thumbnail URL", placeholder="Enter a thumbnail URL. Only HTTP(S) is supported", required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.set_image(url=self.url.value)
        self.embed.set_thumbnail(url=self.thumbnail.value)
        await interaction.edit_original_response(content="", embed=self.embed)


class AddFieldModal(ui.Modal, title="Embed Add Field Editor"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.inline.default = "True"
        super().__init__()

    name = ui.TextInput(label="Field Name", placeholder="The field name. Required", max_length=256)
    value = ui.TextInput(label="Value", placeholder="The embed value.", max_length=1024, style=discord.TextStyle.paragraph)
    inline = ui.TextInput(
        label="Inline?", placeholder="Do you want it to be inline? Yes/No/True/False", required=False, max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.add_field(name=self.name.value, value=self.value.value, inline=to_bool(self.inline.value))
        await interaction.edit_original_response(content="", embed=self.embed)


class RemoveFieldModal(ui.Modal, title="Embed Remove Field Modal"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        super().__init__()

    index = ui.TextInput(
        label="Index", placeholder="The field to remove. To calculate index, count each field, starting from 0"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.remove_field(index=int(self.index.value))
        await interaction.edit_original_response(content="", embed=self.embed)


class UpdateExistingFieldModal(ui.Modal, title="Update Existing Field"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.inline.default = True
        super().__init__()

    index = ui.TextInput(
        label="Index", placeholder="The index of the item to edit. To calculate index, count each field, starting from 0"
    )
    name = ui.TextInput(label="Name", placeholder="The new name", max_length=256)
    value = ui.TextInput(label="Value", placeholder="The new value", max_length=1024, style=discord.TextStyle.paragraph)
    inline = ui.TextInput(label="Inline", placeholder="The new inline status", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.set_field_at(
            index=int(self.index.value), name=self.name.value, value=self.value.value, inline=to_bool(self.inline.value)
        )
        await interaction.edit_original_response(content="", embed=self.embed)


class UpdateExistingFieldModal2(ui.Modal, title="Update Existing Field"):
    def __init__(self, embed: discord.Embed, index: int):
        self.embed = embed
        self.field = embed.fields[index]
        self.index = index
        self.name.default = self.field.name
        self.value.default = self.field.value
        self.inline.default = self.field.inline
        super().__init__()

    # index = ui.TextInput(
    #    label="Index", placeholder="The index of the item to edit. To calculate index, count each field, starting from 0"
    # )
    name = ui.TextInput(label="Name", placeholder="The new name", max_length=256)
    value = ui.TextInput(label="Value", placeholder="The new value", max_length=1024, style=discord.TextStyle.paragraph)
    inline = ui.TextInput(label="Inline", placeholder="The new inline status", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.embed.set_field_at(
            index=int(self.index), name=self.name.value, value=self.value.value, inline=to_bool(self.inline.value)
        )
        await interaction.edit_original_response(
            content="", embed=self.embed, view=EmbedEditView(interaction.user, self.embed)
        )


class SendView(ui.View):
    def __init__(self, original_author: discord.User, embed: discord.Embed):
        self.original_author = original_author
        self.embed = embed
        super().__init__()

    @ui.select(cls=ui.ChannelSelect, channel_types=[discord.ChannelType.text], max_values=1)
    async def channel_select(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        if self.original_author != interaction.user:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
        channel: discord.TextChannel = interaction.guild.get_channel(select.values[0].id)
        perms = channel.permissions_for(interaction.user)
        if perms.send_messages and perms.embed_links:
            perms = channel.permissions_for(interaction.guild.me)
            if perms.send_messages and perms.embed_links:
                await channel.send(embed=self.embed)
            else:
                return await interaction.response.send_message(
                    "I cannot send messages in the target channel!", ephemeral=True
                )
        else:
            return await interaction.response.send_message("You cannot send messages in the target channel!", ephemeral=True)
        await interaction.response.send_message(f"Sent to {channel.mention}!", ephemeral=True)

    @ui.button(label="<- Back")
    async def go_back(self, interaction: discord.Interaction, button: discord.Button):
        if not interaction.user == self.original_author:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)
        await interaction.response.defer()
        view = EmbedEditView(interaction.user, embed=self.embed)
        await interaction.edit_original_response(view=view)


class SaveToBotModal(ui.Modal, title="Save Embed to Bot Menu"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        super().__init__()

    name = ui.TextInput(label="Name", placeholder="The name of the embed to put in the bot")

    async def on_submit(self, interaction: discord.Interaction):
        content = json.dumps(self.embed.to_dict())
        num = len(await interaction.client.db.fetch("SELECT * FROM userembeds WHERE ownerID=$1", interaction.user.id))
        await interaction.client.db.execute(
            """
        INSERT INTO userembeds(ownerID, userembedno, name, content )
        VALUES($1, $2, $3, $4)
        """,
            interaction.user.id,
            num,
            self.name.value,
            content,
        )
        await interaction.response.send_message("Saved embed to bot!", ephemeral=True)


class sendToWebhook(ui.Modal, title="Send Embed to Webhook"):
    def __init__(self, embed: discord.Embed):
        self.embed = embed
        super().__init__()

    content = ui.TextInput(
        label="Content",
        placeholder="Message content to send with the embed.",
        required=False,
        style=discord.TextStyle.paragraph,
    )
    webhook = ui.TextInput(label="Webhook", placeholder="The webhook to send to.")
    name = ui.TextInput(
        label="Webhook name", placeholder="The username for the webhook. Defaults to webhook name.", required=False
    )
    avatar_url = ui.TextInput(
        label="Webhook Avatar URL", placeholder="The avatar url for the webhook. Defaults to webhook avatar", required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(url=self.webhook.value, session=session)
                await webhook.send(
                    self.content.value, embed=self.embed, username=self.name.value, avatar_url=self.avatar_url.value
                )
        except ValueError:
            return await interaction.response.send_message("Invalid webhook URL given.", ephemeral=True)
        await interaction.response.send_message("Sent!")


class ConfirmEmbedDelete(ui.View):
    def __init__(self, original_author: discord.User, number: int):
        self.original_author = original_author
        self.number = number

    @ui.button(label="Confirm and Delete", style=discord.ButtonStyle.danger)
    async def delete_saved_embed(self, interaction: discord.Interaction, button: ui.Button):
        if self.original_author != interaction.user:
            return await interaction.response.send_message("This is not for you", ephemeral=True)
        await interaction.client.db.execute(
            "DELETE FROM userembeds WHERE id=$1 AND userembedno=$2", interaction.user.id, self.number
        )
        await interaction.response.send_message("Deleted embed!")

    @ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if self.original_author != interaction.user:
            return await interaction.response.send_message("This is not for you", ephemeral=True)
        await interaction.response.defer()
        await interaction.edit_original_response(view=None)


class LoadEmbedFromTextModal(ui.Modal, title="Load Embed From File Contents Menu"):
    def __init__(self, edit: bool):
        self.edit = edit
        super().__init__()

    filecontents = ui.TextInput(
        label="File Contents", style=discord.TextStyle.long, placeholder="Input the contents of the .json/.txt file"
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed.from_dict(json.loads(self.filecontents.value))
        view = None
        if self.edit:
            view = EmbedEditView(interaction.user, embed)
        await interaction.response.send_message(embed=embed, view=view)


class SelectEmbedToEditView(ui.View):
    def __init__(
        self, message: Union[discord.Message, discord.WebhookMessage], original_author: Union[discord.Member, discord.User]
    ):
        super().__init__()
        self.message = message
        self.original_author = original_author
        current = 0
        for embed in message.embeds:
            self.embed_select.add_option(label=f"Embed #{current} - {embed.title}", value=current)
            current += 1

    @ui.select(placeholder="The embed to edit", min_values=1, max_values=1)
    async def embed_select(self, interaction: discord.Interaction, select: ui.Select):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This is not for you!")
        await interaction.response.defer()
        embed = self.message.embeds[int(select.values[0])]
        view = EmbedEditView(interaction.user, embed)
        await interaction.edit_original_response(content="", embed=embed, view=view)
        view.message = await interaction.original_response()


class Embed(commands.GroupCog, name="embed"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.edit_embed_from_message = app_commands.ContextMenu(name="Edit Embed", callback=self.update_from_message)
        self.bot.tree.add_command(self.edit_embed_from_message)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.edit_embed_from_message, type=self.edit_embed_from_message.type)

    async def update_from_message(self, interaction: discord.Interaction, message: discord.Message):
        if len(message.embeds) == 0:
            return await interaction.response.send_message("There are no embeds in this message to edit!", ephemeral=True)
        elif len(message.embeds) == 1:
            embed = message.embeds[0]
            view = EmbedEditView(interaction.user, embed)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            view = SelectEmbedToEditView(message, interaction.user)
            await interaction.response.send_message("Select the embed to edit", view=view, ephemeral=True)

    @app_commands.command(name="create", description="Create an embed")
    @app_commands.describe(ephemeral="Allow other users to see it? True = Hide, False = Show. Defaults to False")
    async def create_embed(self, interaction: discord.Interaction, ephemeral: bool = False):
        embed = discord.Embed(
            title="Dog Knife's Embed Creator.",
            description="""This is dogknife's embed creator.
            
            This supports markdown such as *italics*, **bold**, __underline__, ~~strikethrough~~ and more!
            
            ```Codeblocks are also supported
            
            Have fun!```

            This field can support up to 4000 characters.
            """,
        )
        view = EmbedEditView(interaction.user, embed)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral, view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="list", description="List all of your embeds")
    async def list_user_embed(self, interaction: discord.Interaction):
        results = await interaction.client.db.fetch("SELECT * FROM userembeds WHERE ownerID=$1", interaction.user.id)
        embeds = {}
        for i in range(len(results)):
            embeds[i] = {"name": results[i]["name"], "number": results[i]["userembedno"]}
        await interaction.response.send_message(f"{embeds}")

    @app_commands.command(name="load", description="Load one of your embeds! After loaded, the edit menu loads")
    @app_commands.describe(
        number="The embed number to load. Starts at zero. Use `/embeds list` to view your embeds!",
        edit="Show the edit and send menu? Defaults to false",
    )
    async def load_user_embed(self, interaction: discord.Interaction, number: int, edit: bool = False):
        results = await interaction.client.db.fetchval(
            "SELECT content FROM userembeds WHERE ownerID=$1 AND userembedno=$2", interaction.user.id, number
        )
        embed = discord.Embed.from_dict(json.loads(results))
        view = None
        if edit:
            view = EmbedEditView(interaction.user, embed)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="delete", description="Delete one of your embeds!")
    @app_commands.describe(number="The number to delete")
    async def delete_user_embed(self, interaction: discord.Interaction, number: int):
        results = await interaction.client.db.fetchval(
            "SELECT content FROM userembeds WHERE ownerID=$1 AND userembedno=$2", interaction.user.id, number
        )
        embed = discord.Embed.from_dict(json.loads(results))
        view = ConfirmEmbedDelete(interaction.user, number)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="file", description="Load an embed from a file. Expects `.json`")
    @app_commands.describe(
        file="The file to load the embed from. Leaving this empty will give you a prompt to paste into.",
        edit="Open edit and send menu? Defaults to false",
    )
    async def load_embed_from_file(
        self, interaction: discord.Interaction, file: discord.Attachment = None, edit: bool = False
    ):
        if file:
            if file.content_type.split(";")[0] != "application/json" and file.content_type.split(";")[0] != "text/plain":
                return await interaction.response.send_message("Invalid file type", ephemeral=True)
            await interaction.response.defer()
            contents = await file.read()
            embed = discord.Embed.from_dict(json.loads(contents))
            view = None
            if edit:
                view = EmbedEditView(interaction.user, embed)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.send_modal(LoadEmbedFromTextModal(edit))

    @app_commands.command(name="link", description="Create a custom URL invite")
    @app_commands.default_permissions(embed_links=True)
    @app_commands.describe(url="The URL to use. This cannot be changed later")
    async def create_link_embed(self, interaction: discord.Interaction, url: str, ephemeral: bool = False):
        embed = discord.Embed(type="link", title="Link Embed", description="A brief description about your url.", url=url)
        view = EmbedEditView(interaction.user, embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=ephemeral)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(Embed(bot))
