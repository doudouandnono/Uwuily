from __future__ import annotations

import random
import string
import typing as t
from datetime import datetime, timedelta

from discord.ext import commands
from loguru import logger

import helpers.constant as constant
import helpers.custom_check as custom_check
import helpers.message as message
import helpers.pillow as pillow
import views.wish_view as wish_view
from models.anicard import Anicard
from models.user import User

if t.TYPE_CHECKING:
    import asyncpg
    import discord
    from PIL import Image

    from launcher import Uwuily


class AnicardCog(commands.Cog):
    def __init__(self, bot: Uwuily) -> None:
        self.bot: Uwuily = bot

    """
    ############################################################
    WISH
    ############################################################
    """

    async def can_make_wish(self, ctx: commands.Context, last_wish_time: datetime, current_time: datetime) -> bool:
        cooldown_ready_time = last_wish_time + timedelta(seconds=constant.Cooldown.WISH)
        if current_time < cooldown_ready_time:
            time_differences = cooldown_ready_time - current_time
            hours = time_differences.seconds // 3600
            minutes = (time_differences.seconds // 60) % 60
            cooldown_time = f"{hours}H{minutes}M" if hours > 0 else f"{minutes}M"
            await message.Send.error(
                ctx=ctx,
                message=(
                    "You can only make a wish once every 24 hours.\n"
                    f"Please wait `{cooldown_time}` before making another wish."
                ),
            )
            return False
        return True

    async def update_last_wish_time(self, ctx: commands.Context, current_time: datetime) -> None:
        await ctx.bot.db.execute(
            """
                UPDATE user_cooldowns
                SET last_wish_ts = $1
                WHERE user_id = $2
            """,
            current_time,
            ctx.author.id,
        )

    async def get_anicards(self, ctx: commands.Context, amount: int = 3) -> list[Anicard]:
        query: list[asyncpg.Record] = await ctx.bot.db.fetch(
            """
                WITH selected_minions AS (
                    SELECT minion_id
                    FROM minions
                    ORDER BY RANDOM ()
                    LIMIT $1
                )
                UPDATE minions
                SET current_codex = current_codex + 1
                WHERE minion_id IN (
                    SELECT minion_id
                    FROM selected_minions
                )
                RETURNING minion_id, character, anime, original_aniclass, current_codex
            """,
            amount,
        )
        anicard_data: list[dict[str, t.Any]] = [dict(record) for record in query]
        anicards = []
        for data in anicard_data:
            random_tag = "".join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=random.randint(*(4, 6)),
                ),
            ).upper()
            anicard = Anicard(
                minion_id=data["minion_id"],
                tag=random_tag,
                character=data["character"],
                anime=data["anime"],
                is_shattered=False,
                image_ver=1,
                frame="T1",
                aniclass=data["original_aniclass"],
                codex=data["current_codex"],
            )
            anicards.append(anicard)
        return anicards

    async def draw_wish_canvas(self, anicards: list[Anicard]) -> discord.File:
        wish_canvas_image_path = "assets/anicard/canvas.png"
        wish_canvas: Image.Image = await pillow.get_image(image_path=wish_canvas_image_path)
        for index, anicard in enumerate(anicards):
            anicard_image: Image.Image = await anicard.draw_anicard()
            x_position = 11 + (index * 465)
            y_position = -10
            wish_canvas.paste(anicard_image, (x_position, y_position), mask=anicard_image)
        wish_file = pillow.buffer_bytes(image=wish_canvas)
        return wish_file

    async def add_wish_button(
        self,
        ctx: commands.Context,
        anicards: list[Anicard],
        view: discord.ui.View,
        current_time: datetime,
    ) -> None:
        for anicard in anicards:
            item = wish_view.WishButton(
                ctx=ctx,
                minion_id=anicard.minion_id,  # type: ignore
                character=anicard.character,  # type: ignore
                aniclass=anicard.aniclass,  # type: ignore
                codex=int(anicard.codex),  # type: ignore
                tag=anicard.tag,  # type: ignore
                current_time=current_time,
            )
            view.add_item(item=item)

    @commands.hybrid_command(
        name="wish",
        aliases=["w"],
        description="Wish for one of the three randomly presented Anicards.",
    )
    @commands.cooldown(1, constant.Cooldown.COMMAND, commands.BucketType.user)
    @custom_check.is_registered()
    @logger.catch
    async def wish(self, ctx: commands.Context) -> None:
        user = User(user_id=ctx.author.id)
        await user.fetch_data(ctx=ctx, get_cooldowns=True)

        current_time = datetime.utcnow()
        last_wish_time: datetime = user.cooldowns["last_wish_ts"]
        can_make_wish: bool = await self.can_make_wish(
            ctx=ctx,
            last_wish_time=last_wish_time,
            current_time=current_time,
        )
        if not can_make_wish:
            return None
        await self.update_last_wish_time(ctx=ctx, current_time=current_time)

        anicards: list[Anicard] = await self.get_anicards(ctx=ctx, amount=3)
        wish_image_file: discord.File = await self.draw_wish_canvas(anicards=anicards)
        view = wish_view.WishView(ctx=ctx)
        await self.add_wish_button(ctx=ctx, anicards=anicards, view=view, current_time=current_time)

        view.view_message = await ctx.send(
            content=f"{ctx.author.mention} Select an Anicard!",
            file=wish_image_file,
            view=view,
        )


async def setup(bot: Uwuily) -> None:
    await bot.add_cog(AnicardCog(bot))
