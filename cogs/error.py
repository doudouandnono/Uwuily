from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from helpers.constant import CustomColors
from helpers.custom_check import NotRegistered
from helpers.message import Send
from models.user import User
from views.confirm_view import send_confirm_view

if TYPE_CHECKING:
    from launcher import Uwuily


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot: Uwuily) -> None:
        self.bot: Uwuily = bot
        self.error_handlers = {
            commands.CommandNotFound: self.handle_command_not_found,
            commands.MissingRequiredArgument: self.handle_missing_required_argument,
            commands.BadArgument: self.handle_bad_argument,
            commands.CommandOnCooldown: self.handle_command_on_cooldown,
            NotRegistered: self.handle_not_registered,
        }

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        handler = self.error_handlers.get(type(error))  # type: ignore
        if handler:
            await handler(ctx, error)
        else:
            raise error

    async def handle_command_not_found(self, _: commands.Context, __: commands.CommandNotFound) -> None:
        return None

    async def handle_missing_required_argument(
        self,
        ctx: commands.Context,
        _: commands.MissingRequiredArgument,
    ) -> None:
        if ctx.command:
            command_name = ctx.command.name
            command_signature = ctx.command.signature
            await Send.error(
                ctx=ctx,
                message=f"Missing required argument(s). \n`Usage: UwU {command_name} {command_signature}`.",
            )

    async def handle_bad_argument(self, ctx: commands.Context, _: commands.BadArgument) -> None:
        await ctx.send_help(ctx.command)

    async def handle_command_on_cooldown(self, ctx: commands.Context, error: commands.CommandOnCooldown) -> None:
        if await ctx.bot.is_owner(ctx.author):
            if ctx.command:
                ctx.command.reset_cooldown(ctx)
            await ctx.bot.process_commands(ctx.message)
            return None
        cooldown_period = int(error.retry_after)
        await Send.error(
            ctx=ctx,
            message=f"You are on cooldown for this command. Please try again in `{cooldown_period}S`.",
        )

    async def handle_not_registered(self, ctx: commands.Context, _: NotRegistered) -> None:
        welcome_embed = discord.Embed(
            title="Welcome to Uwuily Bot!",
            description=(
                "To start playing, we need your permission to store your Discord account's "
                "User ID and interact with any chat messages you send that contain the word UwU."
            ),
            color=CustomColors.BLUE,
        )
        if self.bot.user:
            welcome_embed_thumbnail = self.bot.user.avatar
            welcome_embed.set_thumbnail(url=welcome_embed_thumbnail)

        register_confirm_result: bool | None = await send_confirm_view(
            ctx=ctx,
            message=ctx.author.mention,
            embed=welcome_embed,
        )
        if not register_confirm_result:
            return None
        user = User(user_id=ctx.author.id)
        await user.register(ctx=ctx)

        thankyou_embed = discord.Embed(
            title="Thank you for accepting our terms!",
            description=(
                "Join our [Support Server](https://discord.gg/FvegU7Vdx5) to play Uwuily Bot with other players, "
                "and visit our [Wiki](https://uwuily.gitbook.io) for tutorial on how to get started!\n"
                "We hope you enjoy playing Uwuily Bot!"
            ),
            color=CustomColors.YELLOW,
        )
        await ctx.send(content=ctx.author.mention, embed=thankyou_embed)


async def setup(bot: Uwuily) -> None:
    """Load the Error Handler cog."""

    await bot.add_cog(ErrorHandlerCog(bot))
