import typing

import discord
from discord import app_commands, ui
from discord.ext import commands


class MainView(ui.View):
    def __init__(self, original_author: discord.User):
        super().__init__(timeout=300)
        self.original_author = original_author
        self.calculation = {
            "digit1": None,
            "operation": None,
            "digit2": None,
            #'answer': None
        }

    def generate_message(self):
        # return self.calculation
        return f"{self.calculation['digit1']} {self.calculation['operation'] or ''} {self.calculation['digit2'] or ''}"

    def edit_number(self, number: int):
        if self.calculation["digit1"] is None:
            self.calculation["digit1"] = number
        elif self.calculation["digit1"] is not None and self.calculation["operation"] is None:
            s = str(self.calculation["digit1"]) + str(number)
            self.calculation["digit1"] = int(s)
        elif self.calculation["operation"] is not None and self.calculation["digit2"] is None:
            self.calculation["digit2"] = number
        else:
            s = str(self.calculation["digit2"]) + str(number)
            self.calculation["digit2"] = int(s)

    def solve(self) -> typing.Union[int, bool]:
        result = None
        if self.calculation["operation"] == "+":
            result = self.calculation["digit1"] + self.calculation["digit2"]
        elif self.calculation["operation"] == "-":
            result = self.calculation["digit1"] - self.calculation["digit2"]
        elif self.calculation["operation"] == "*":
            result = self.calculation["digit1"] * self.calculation["digit2"]
        elif self.calculation["operation"] == "/":
            result = self.calculation["digit1"] / self.calculation["digit2"]
        elif self.calculation["digit1"] and self.calculation["operation"] is None:
            result = self.calculation["digit1"]
        else:
            return 0
        self.calculation["digit1"] = result
        self.calculation["digit2"] = None
        self.calculation["operation"] = None
        return result

    @ui.button(label="‎ ", disabled=True, row=0)
    async def blank(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a placeholder, it does nothing.")

    @ui.button(label="‎ ", disabled=True, row=0)
    async def blank2(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a placeholder, it does nothing.")

    @ui.button(label="C", custom_id="clear", row=0, style=discord.ButtonStyle.danger)
    async def clear_calculator(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.calculation["digit1"] = None
        self.calculation["operation"] = None
        self.calculation["digit2"] = None
        await interaction.edit_original_response(content="Calculator Empty")

    @ui.button(label="/", custom_id="divsion", row=0)
    async def division_operation(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.calculation["operation"] = "/"
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="7", custom_id="7", row=1)
    async def add_number_seven(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="8", custom_id="8", row=1)
    async def add_number_eight(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="9", custom_id="9", row=1)
    async def add_number_nine(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="X", custom_id="multiply", row=1)
    async def mutiply_operation(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.calculation["operation"] = "*"
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="4", custom_id="4", row=2)
    async def add_number_four(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="5", custom_id="5", row=2)
    async def add_number_five(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="6", custom_id="6", row=2)
    async def add_number_six(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="-", custom_id="subtract", row=2)
    async def subtraction_operation(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.calculation["operation"] = "-"
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="1", custom_id="1", row=3)
    async def add_number_one(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="2", custom_id="2", row=3)
    async def add_number_two(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="3", custom_id="3", row=3)
    async def add_number_three(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="+", custom_id="add", row=3)
    async def addition_operation(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.calculation["operation"] = "+"
        await interaction.edit_original_response(content=self.generate_message())

    @ui.button(label="0", custom_id="0", row=4)
    async def add_number_zero(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user != self.original_author:
            return await interaction.response.send_message("This message is not for you.", ephemeral=True)
        await interaction.response.defer()
        self.edit_number(int(button.custom_id))
        await self.message.edit(content=self.generate_message())

    @ui.button(label="‎ ", disabled=True, row=4)
    async def blank3(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("This is a placeholder, it does nothing.")

    @ui.button(label="‎ ", disabled=True, row=4)
    async def blank4(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("This is a placeholder, it does nothing.")

    @ui.button(label="=", row=4)
    async def solve_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.edit_original_response(content=self.solve())


class Calculator(commands.GroupCog, name="calculator"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ui", description="Shows the calculator UI")
    async def calculator_ui(self, interaction: discord.Interaction):
        view = MainView(interaction.user)
        await interaction.response.defer()
        await interaction.edit_original_response(content="Caculator Empty", view=view)
        view.message = await interaction.original_response()

    @app_commands.command(
        name="add", description="Adds two numbers. If you are doing more complex problems, consider using UI instead."
    )
    @app_commands.describe(
        num1="The first number", num2="The second number", ephemeral="If you're bad at math and you want this to be private."
    )
    async def calculator_add(self, interaction: discord.Interaction, num1: int, num2: int, ephemeral: bool = False):
        result = num1 + num2
        await interaction.response.send_message(f"{num1} + {num2} = {result}", ephemeral=ephemeral)

    @app_commands.command(
        name="subtract",
        description="Subtracts two numbers. If you are doing more complex problems, consider using UI instead.",
    )
    @app_commands.describe(
        num1="The first number", num2="The second number", ephemeral="If you're bad at math and you want this to be private."
    )
    async def calculator_subtract(self, interaction: discord.Interaction, num1: int, num2: int, ephemeral: bool = False):
        result = num1 - num2
        await interaction.response.send_message(f"{num1} - {num2} = {result}", ephemeral=ephemeral)

    @app_commands.command(
        name="multiply",
        description="Multiplies two numbers. If you are doing more complex problems, consider using UI instead.",
    )
    @app_commands.describe(
        num1="The first number", num2="The second number", ephemeral="If you're bad at math and you want this to be private."
    )
    async def calculator_multiply(self, interaction: discord.Interaction, num1: int, num2: int, ephemeral: bool = False):
        result = num1 * num2
        await interaction.response.send_message(f"{num1} * {num2} = {result}", ephemeral=ephemeral)

    @app_commands.command(
        name="divide", description="Divides two numbers. If you are doing more complex problems, consider using UI instead."
    )
    @app_commands.describe(
        num1="The first number", num2="The second number", ephemeral="If you're bad at math and you want this to be private."
    )
    async def calculator_divide(self, interaction: discord.Interaction, num1: int, num2: int, ephemeral: bool = False):
        result = num1 / num2
        await interaction.response.send_message(f"{num1} / {num2} = {result}", ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(Calculator(bot))
