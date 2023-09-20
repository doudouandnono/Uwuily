from discord.ext import commands


class NotRegistered(commands.CheckFailure):
    pass


def is_registered():  # noqa: ANN201
    async def is_registered_check(ctx: commands.Context) -> bool:
        is_registered: bool = await ctx.bot.db.fetchval(
            """
            SELECT EXISTS(
                SELECT 1
                FROM users
                WHERE user_id = $1
            )
            """,
            ctx.author.id,
        )
        if not is_registered:
            raise NotRegistered()
        return True

    return commands.check(is_registered_check)
