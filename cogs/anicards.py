from __future__ import annotations

import random
import string
import typing as t
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from loguru import logger

import helpers.constant as constant
import helpers.custom_check as custom_check
import helpers.message as message
import helpers.pillow as pillow
import views.pagination_view as pagination_view
import views.wish_view as wish_view
from models.anicard import Anicard
from models.user import User

if t.TYPE_CHECKING:
    import asyncpg
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

    """
    ############################################################
    COLLECTION
    ############################################################
    """

    ANICLASS_PREFIX = {
        "a": "⚜",
        "artisan": "⚜",
        "c": "⚔",
        "combatant": "⚔",
        "g": "☄",
        "gatherer": "☄",
    }

    ORDER_PREFIX = {
        "c": "character",
        "character": "character",
        "cd": "codex",
        "codex": "codex",
    }

    PREFIX_MAP = {
        "c": ("character", lambda key: key.title()),
        "character": ("character", lambda key: key.title()),
        "a": ("aniclass", lambda key: AnicardCog.ANICLASS_PREFIX.get(key, None)),
        "aniclass": ("aniclass", lambda key: AnicardCog.ANICLASS_PREFIX.get(key, None)),
        "o": ("order", lambda key: AnicardCog.ORDER_PREFIX.get(key, "obtained_ts")),
        "order": ("order", lambda key: AnicardCog.ORDER_PREFIX.get(key, "obtained_ts")),
    }

    def parse_filter(self, collection_filter: str | None) -> dict[str, str]:
        parsed_filter = {
            "character": None,
            "aniclass": None,
            "order": "obtained_ts",
        }
        if not collection_filter:
            return parsed_filter
        conditions = collection_filter.split(" ")
        for condition in conditions:
            prefix, key = condition.lower().split(":", 1)
            if prefix in self.PREFIX_MAP:
                field, transform = self.PREFIX_MAP[prefix]
                parsed_filter[field] = transform(key)
        return parsed_filter

    def apply_filter(self, collection: list[Anicard], parsed_filter: dict[str, str]) -> list[Anicard]:
        if parsed_filter["character"]:
            collection = [minion for minion in collection if parsed_filter["character"] in str(minion.character)]
        if parsed_filter["aniclass"]:
            collection = [minion for minion in collection if parsed_filter["aniclass"] == minion.aniclass]
        if parsed_filter["order"]:
            collection = sorted(collection, key=lambda minion: getattr(minion, parsed_filter["order"]))
        return collection

    def paginate_collection(self, ctx: commands.Context, collection: list[Anicard]) -> list[discord.Embed]:
        formatted_anicard_data = []
        for anicard in collection:
            minion_text = f"`[{anicard.aniclass} {anicard.codex}] {anicard.character}` • `Tier {anicard.tier}` • `{anicard.tag}`\n"
            if anicard.is_shattered:
                minion_text = f"*~~{minion_text}~~*"
            formatted_anicard_data.append(minion_text)
        # Split the formatted_anicard_data into sublist of 10.
        embed_description_sublist = [
            formatted_anicard_data[n : n + 10] for n in range(0, len(formatted_anicard_data), 10)
        ]
        # Turn each sublist into an embed page.
        embed_pages = []
        for index, page in enumerate(embed_description_sublist):
            embed_description = "".join(page)
            embed_title = f"{ctx.author.name.title()}'s Anicard Collections"
            collection_embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=constant.CustomColors.BLUE,
            )
            footer_text = f"Page ({index+1}/{len(embed_description_sublist)})"
            collection_embed.set_footer(text=footer_text)
            embed_pages.append(collection_embed)
        return embed_pages

    @commands.hybrid_command(
        name="collection",
        aliases=["c"],
        description="View your Anicard collection.",
    )
    @commands.cooldown(1, constant.Cooldown.COMMAND, commands.BucketType.user)
    @custom_check.is_registered()
    @logger.catch
    async def collection(self, ctx: commands.Context, *, collection_filter: str | None) -> None:
        user = User(user_id=ctx.author.id)
        await user.fetch_data(ctx=ctx, get_anicards=True)
        if not user.anicards:
            await message.Send.error(
                ctx=ctx,
                message=("You do not have any Anicards in your collection! Try wishing for one by typing `uwu wish`."),
            )
            return None

        parsed_filter: dict[str, str] = self.parse_filter(collection_filter=collection_filter)
        filtered_collection: list[Anicard] = self.apply_filter(
            collection=user.anicards,
            parsed_filter=parsed_filter,
        )
        if not filtered_collection:
            await message.Send.error(
                ctx=ctx,
                message="No Anicards found with the given filter. Try again with a different filter.",
            )
            return None
        paginated_collection: list[discord.Embed] = self.paginate_collection(
            ctx=ctx,
            collection=filtered_collection,
        )

        view = pagination_view.PaginationView(ctx=ctx, embeds=paginated_collection)
        view.view_message = await ctx.send(content=ctx.author.mention, embed=paginated_collection[0], view=view)


async def setup(bot: Uwuily) -> None:
    await bot.add_cog(AnicardCog(bot))
