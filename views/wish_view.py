from datetime import datetime

import asyncpg
import discord
from discord.ext import commands

import helpers.message as message


class WishView(discord.ui.View):
    def __init__(self, ctx: commands.Context) -> None:
        super().__init__(timeout=300)
        self.ctx = ctx
        self.view_message: discord.Message

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore
        timeout_message = f"{self.ctx.author.mention} {message.MessageTemplate.VIEW_EXPIRED}"
        await self.view_message.edit(content=timeout_message, view=self)


class WishButton(discord.ui.Button):
    def __init__(
        self,
        ctx: commands.Context,
        minion_id: int,
        character: str,
        aniclass: str,
        codex: int,
        tag: str,
        current_time: datetime,
    ) -> None:
        super().__init__(label=character.title())
        self.ctx = ctx
        self.minion_id = minion_id
        self.character = character
        self.aniclass = aniclass
        self.codex = codex
        self.tag = tag
        self.current_time = current_time

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.ctx.author.id:
            error_message = f"{interaction.user.mention} {message.MessageTemplate.VIEW_NOT_AUTHOR}"
            await interaction.followup.send(content=error_message, ephemeral=True)
            return None

        if not interaction.response.is_done():
            await interaction.response.defer()

        self.style = discord.ButtonStyle.blurple
        for item in self.view.children:  # type: ignore
            item.disabled = True
        await interaction.message.edit(view=self.view)  # type: ignore

        try:
            await self.ctx.bot.db.execute(
                """
                INSERT INTO user_anicards(
                    user_id,
                    minion_id,
                    tag,
                    obtained_ts,
                    aniclass,
                    codex
                )
                VALUES($1, $2, $3, $4, $5, $6)
                """,
                self.ctx.author.id,
                self.minion_id,
                self.tag,
                self.current_time,
                self.aniclass,
                self.codex,
            )
        except asyncpg.UniqueViolationError:
            await self.ctx.send("gglol")
            return None

        wish_success_message = f"`{self.character}` with Tag of `{self.tag}` has been added to your collection!"
        await message.Send.success(ctx=self.ctx, message=wish_success_message)
