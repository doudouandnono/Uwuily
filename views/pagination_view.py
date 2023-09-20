import discord
from discord.ext import commands

import helpers.message as message


class PaginationView(discord.ui.View):
    """Pagination view for embeds."""

    def __init__(self, ctx: commands.Context, embeds: list[discord.Embed]) -> None:
        super().__init__(timeout=300)
        self.ctx = ctx
        self.view_message: discord.Message
        self.embeds = embeds
        self.current_embed_pagenumber = 0
        self.first_page.disabled = True
        self.previous_page.disabled = True
        self.next_page.disabled = len(self.embeds) == 1
        self.last_page.disabled = len(self.embeds) == 1

        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i+1} of {len(self.embeds)}")

    async def on_timeout(self) -> None:
        """Actions after timeout."""

        for item in self.children:
            item.disabled = True  # type: ignore
        timeout_message = f"{self.ctx.author.mention} {message.MessageTemplate.VIEW_EXPIRED}"
        await self.view_message.edit(content=timeout_message, view=self)

        return None

    @discord.ui.button(
        emoji="⏪",
        style=discord.ButtonStyle.blurple,
    )
    async def first_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Go to the first page."""

        self.current_embed_pagenumber = 0
        embed = self.embeds[self.current_embed_pagenumber]

        self.first_page.disabled = True
        self.previous_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        emoji="◀",
        style=discord.ButtonStyle.blurple,
    )
    async def previous_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Go to the previous page."""

        self.current_embed_pagenumber -= 1
        embed = self.embeds[self.current_embed_pagenumber]

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.current_embed_pagenumber == 0:
            self.first_page.disabled = True
            self.previous_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        emoji="▶",
        style=discord.ButtonStyle.blurple,
    )
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Go to the next page."""

        self.current_embed_pagenumber += 1
        embed = self.embeds[self.current_embed_pagenumber]

        self.first_page.disabled = False
        self.previous_page.disabled = False
        if self.current_embed_pagenumber == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        emoji="⏩",
        style=discord.ButtonStyle.blurple,
    )
    async def last_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Go to the last page."""

        self.current_embed_pagenumber = len(self.embeds) - 1
        embed = self.embeds[self.current_embed_pagenumber]

        self.first_page.disabled = False
        self.previous_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
