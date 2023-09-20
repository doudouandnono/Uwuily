import discord
from discord.ext import commands

from helpers.message import MessageTemplate


class ConfirmView(discord.ui.View):
    def __init__(self, ctx: commands.Context) -> None:
        super().__init__(timeout=300)
        self.ctx = ctx
        self.view_message: discord.Message
        self.result = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore
        await self.view_message.edit(
            content=f"{self.ctx.author.mention} {MessageTemplate.VIEW_EXPIRED}",
            view=self,
        )

    @discord.ui.button(label="YES", style=discord.ButtonStyle.gray)
    async def accept_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.followup.send(
                content=f"{interaction.user.mention} {MessageTemplate.VIEW_NOT_AUTHOR}",
                ephemeral=True,
            )
            return None

        if not interaction.response.is_done():
            await interaction.response.defer()

        button.style = discord.ButtonStyle.green
        for item in self.children:
            item.disabled = True  # type: ignore
        await interaction.message.edit(view=self)  # type: ignore

        self.result = True
        self.stop()

    @discord.ui.button(label="NO", style=discord.ButtonStyle.gray)
    async def decline_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.followup.send(
                content=f"{interaction.user.mention} {MessageTemplate.VIEW_NOT_AUTHOR}",
                ephemeral=True,
            )
            return None

        if not interaction.response.is_done():
            await interaction.response.defer()

        button.style = discord.ButtonStyle.red
        for item in self.children:
            item.disabled = True  # type: ignore
        await interaction.message.edit(view=self)  # type: ignore

        self.result = False
        self.stop()

        return None


async def send_confirm_view(ctx: commands.Context, message: str, embed: discord.Embed | None) -> bool | None:
    view = ConfirmView(ctx=ctx)
    view.view_message = await ctx.send(content=message, embed=embed, view=view)  # type: ignore
    await view.wait()
    return view.result
