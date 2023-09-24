from __future__ import annotations

import typing as t

from discord.ext import commands
from loguru import logger

import helpers.constant as constant
import helpers.custom_check as custom_check
import helpers.message as message
from models.user import User

if t.TYPE_CHECKING:
    from launcher import Uwuily
    from models.anicard import Anicard


class MinionCog(commands.Cog):
    def __init__(self, bot: Uwuily) -> None:
        self.bot: Uwuily = bot

    """
    ############################################################
    SUMMON
    ############################################################
    """

    async def try_summon_minion(
        self,
        ctx: commands.Context,
        anicard_tag: str,
        user_anicards: list[Anicard],
        user_max_minion: int,
    ) -> None:
        anicard_tag_data: Anicard | None = next(
            (anicard for anicard in user_anicards if anicard.tag == anicard_tag),
            None,
        )
        if not anicard_tag_data:
            anicard_not_owner_msg = f"You are not the owner of Anicard with tag `{anicard_tag}`!"
            await message.Send.error(ctx=ctx, message=anicard_not_owner_msg)
            return None

        # Check if user already has the minion summoned.
        anicard_tag_character = anicard_tag_data.character
        unique_summon = (
            sum(1 for anicard in user_anicards if anicard.is_summoned and anicard.character == anicard_tag_character)
            < 1
        )
        if not unique_summon:
            unique_summon_msg = f"`{anicard_tag_character}` is already summoned!"
            await message.Send.error(ctx=ctx, message=unique_summon_msg)
            return None

        # Check if the anicard is shattered.
        if anicard_tag_data.is_shattered:
            anicard_shattered_msg = "You can not summon a shattered Anicard!"
            await message.Send.error(ctx=ctx, message=anicard_shattered_msg)
            return None

        # Check if user has reached max minion limit.
        total_summoned = sum(anicard.is_summoned for anicard in user_anicards)  # type: ignore
        if user_max_minion <= total_summoned:
            max_summon_msg = f"You can only summon `{user_max_minion}` minions at a time!"
            await message.Send.error(ctx=ctx, message=max_summon_msg)
            return None

        # Summon the minion.
        await ctx.bot.db.execute(
            """
            UPDATE user_anicards
            SET
                is_summoned = TRUE,
                location = 'Elegrand'
            WHERE anicard_id = $1
            """,
            anicard_tag_data.anicard_id,
        )
        summoned_msg = f"`{anicard_tag_character}` with tag of `{anicard_tag}` has been summoned to `Elegrand`!"
        await message.Send.success(ctx=ctx, message=summoned_msg)

    @commands.hybrid_command(
        name="summon",
        aliases=["s"],
        description="Summon minion to Elegrand.",
    )
    @commands.cooldown(1, constant.Cooldown.COMMAND, commands.BucketType.user)
    @custom_check.is_registered()
    @logger.catch
    async def summon(self, ctx: commands.Context, anicard_tag: str) -> None:
        user = User(user_id=ctx.author.id)
        await user.fetch_data(ctx=ctx, get_anicards=True, get_configs=True)

        anicard_tag = anicard_tag.upper()
        anicards: list[Anicard] = user.anicards
        user_max_minion: int = user.configs["max_minion"]
        await self.try_summon_minion(
            ctx=ctx,
            anicard_tag=anicard_tag,
            user_anicards=anicards,
            user_max_minion=user_max_minion,
        )


async def setup(bot: Uwuily) -> None:
    await bot.add_cog(MinionCog(bot))
