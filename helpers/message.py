from discord.ext import commands

from helpers.constant import CustomEmojis


class MessageTemplate:
    """Template of common messages."""

    # View related messages.
    VIEW_EXPIRED = "This view has expired!"
    VIEW_NOT_AUTHOR = "This message is not for you to interact with!"


class Send:
    @staticmethod
    async def success(ctx: commands.Context, message: str) -> None:
        formatted_message = f"{CustomEmojis.SUCCESS} {ctx.author.mention} {message}"
        await ctx.send(content=formatted_message)

    @staticmethod
    async def error(ctx: commands.Context, message: str) -> None:
        formatted_message = f"{CustomEmojis.ERROR} {ctx.author.mention} {message}"
        await ctx.send(content=formatted_message)
