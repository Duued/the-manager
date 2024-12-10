from typing import Union

import discord
from discord import app_commands, ui
from discord.ext import commands

from cogs import beta


def bool_to_str(input: bool) -> str:
    if input == True:
        return "Yes"
    else:
        return "No"


class ModerateButton(ui.Button["ManageMemberView"]):
    def __init__(self, label: str, style: discord.ButtonStyle, disabled: bool):
        super().__init__(label=label, style=style, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        if self.view.original_author != interaction.user:
            return await interaction.response.send_message("This member management menu is not for you.", ephemeral=True)
        if self.label == "Kick":
            await interaction.response.send_modal(ReasonModal(self))


class ManageMemberView(ui.View):
    message: Union[discord.Message, discord.WebhookMessage]

    def __init__(self, original_author: discord.Member, managed_member: discord.Member):
        super().__init__()
        self.original_author = original_author
        self.managed_member = managed_member

        if original_author.guild_permissions.kick_members and original_author.guild.me.guild_permissions.kick_members:
            if (
                original_author.top_role > managed_member.top_role
                and original_author.guild.me.top_role > managed_member.top_role
                and original_author.guild.owner != managed_member
            ):
                self.add_item(ModerateButton("Kick", discord.ButtonStyle.danger, False))
            else:
                self.add_item(ModerateButton("Kick", discord.ButtonStyle.danger, True))
        else:
            print("Me or author doesn't have kick members")
            self.add_item(ModerateButton("Kick", discord.ButtonStyle.danger, True))
        if original_author.guild_permissions.ban_members and original_author.guild.me.guild_permissions.ban_members:
            if (
                original_author.top_role > managed_member.top_role
                and original_author.guild.me.top_role > managed_member.top_role
                and original_author.guild.owner != managed_member
            ):
                self.add_item(ModerateButton("Ban", discord.ButtonStyle.danger, False))
            else:
                self.add_item(ModerateButton("Ban", discord.ButtonStyle.danger, True))
        else:
            self.add_item(ModerateButton("Ban", discord.ButtonStyle.danger, True))


class ReasonModal(ui.Modal, title="Moderator action modal"):
    def __init__(self, button: ModerateButton):
        super().__init__()
        self.button = button

    reason = ui.TextInput(label="Reason for server removal", max_length=512, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value or "No reason provided"
        if self.button.label == "Kick":
            await self.button.view.managed_member.kick(reason=f"Kicked by {interaction.user.name} ({reason})")
        elif self.button.label == "Ban":
            await self.button.view.managed_member.ban(reason=f"Banned by {interaction.user.name} ({reason})")
        await interaction.response.send_message("Done!", ephemeral=True)
        await self.button.view.message.edit(view=None)


class MemberManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="member", description="Manage a member")
    @app_commands.describe(member="The member to manage")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    @beta.is_beta_i()
    async def member_moderate_menu(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"Managing Member {member.name}", color=0x7289DA)
        embed.add_field(name="Member Started on-boarding", value=bool_to_str(member.flags.started_onboarding))
        embed.add_field(name="Member Completed on-boarding", value=bool_to_str(member.flags.completed_onboarding))
        embed.add_field(name="Suspected Spammer", value=bool_to_str(member.public_flags.spammer))
        text = ""
        for flag in member.public_flags.all():
            text += f"{flag.name}, "
        text = text.rstrip(", ")
        if text == "":
            text = "No Member Flags"
        embed.add_field(name="Member Public Flags", value=text)
        view = ManageMemberView(interaction.user, member)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberManager(bot))
