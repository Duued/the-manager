import traceback

import discord
from discord import app_commands, ui
from discord.ext import commands


class Tree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, exception: app_commands.AppCommandError):
        _view = GetTraceback(exception)
        #tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
        if interaction.command:
            print(f"Error running command {interaction.command.name} by user {interaction.user}")
        print(exception)
        print("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

        try:
            if isinstance(exception, app_commands.MissingPermissions):
                await interaction.channel.send(f"{deny} You do not have permission to run {interaction.command.name}")
            elif isinstance(exception, app_commands.CheckFailure):
                await interaction.channel.send(exception)
            else:
                _view.message = await interaction.response.send_message(exception, view=_view)
        except discord.HTTPException:
            if isinstance(exception, app_commands.MissingPermissions):
                await interaction.channel.send(f"{deny} exception")
            elif isinstance(exception, app_commands.CheckFailure):
                await interaction.channel.send(f"{deny} exception")
            else:
                if await interaction.original_response():
                    await interaction.edit_original_response(content=exception, view=_view)
                else:
                    await interaction.response.send_message(content=exception, view=_view)
                # try:
                #    view.message = await interaction.followup.send(exception, view=view)
                # except:
                #    view.message = await interaction.response.send_message(exception, view=view)


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
        await interaction.message.edit(view=self)
        await interaction.response.defer(ephemeral=False, thinking=False)
        tb = traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__)
        text = "".join(tb)
        p = commands.Paginator(prefix="```py", suffix="```")
        for line in text.splitlines():
            p.add_line(line)
        for page in p.pages:
            await interaction.followup.send(page)
