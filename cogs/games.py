import random

import discord
from discord import app_commands, ui
from discord.ext import commands


class MineButton(discord.ui.Button):
    def __init__(self, label, bad, row):
        self.bad = bad
        super().__init__(style=discord.ButtonStyle.secondary, label=label, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: ui.View = self.view
        text = None
        self.disabled = True
        if self.label == str(self.bad):
            self.style = discord.ButtonStyle.danger
            text = "You lost :("
            for item in view.children:
                item.disabled = True
        else:
            self.style = discord.ButtonStyle.success
            text = "Good"
        disabledbuttons = []
        for item in view.children:
            if item.disabled:
                disabledbuttons.append(item)

        if len(disabledbuttons) == 24 and discord.utils.get(view.children, label=str(self.bad)).disabled is False:
            text = "You win"
            for item in view.children:
                item.disabled = True

        await interaction.edit_original_response(content=text, view=view)


class MineView(discord.ui.View):
    def __init__(self, original_author: discord.User):
        super().__init__(timeout=300)
        self.original_author = original_author

        bad = random.randint(1, 20)
        count = 1
        buttonnumber = 1

        row = 0
        while row <= 4:
            while count <= 5:
                self.add_item(MineButton(buttonnumber, bad, row=row))
                count += 1
                buttonnumber += 1
            row += 1
            count = 1


def int_to_choice(choice: int) -> str:
    if choice == 1:
        return "Rock"
    elif choice == 2:
        return "Paper"
    elif choice == 3:
        return "Scissors"


class RpsButton(discord.ui.Button):
    def __init__(self, label: str, choice: int):
        self.choice = choice
        super().__init__(label=label, style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        status = {}
        await interaction.response.defer()
        status.text = ""
        status.winner = 0
        if self.label == "Rock":
            if self.choice == 1:
                status.text = "Tie!"
                status.winner = 0
            elif self.choice == 2:
                status.text = "GG, I win! I chose paper"
            elif self.choice == 3:
                status.text = "You win! I chose scissors"
        elif self.label == "Paper":
            if self.choice == 1:
                status.text = "GG, I win! I chose rock!"


class RpsView(discord.ui.View):
    def __init__(self, original_author: discord.User):
        self.original_author = original_author
        choice = random.randint(1, 3)
        self.add_item(RpsButton("Rock", choice))
        self.add_item(RpsButton("Paper", choice))
        self.add_item(RpsButton("Scissors", choice))


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mine", description="There is a hidden mine in one of the blocks. This is not minesweeper and is luck."
    )
    async def mine_game(self, interaction: discord.Interaction):
        view = MineView(interaction.user)
        await interaction.response.send_message(content="Good luck.", view=view)

    # @app_commands.command(name="rps", description="Play rock paper scissors against the bot!")
    # async def rps(self, interaction: discord.Interaction):
    #    pass


async def setup(bot):
    await bot.add_cog(Games(bot))
