import typing as t
from pkgutil import iter_modules

import asyncpg
import discord
from decouple import config
from discord.ext import commands
from loguru import logger


class Uwuily(commands.AutoShardedBot):
    def __init__(self, command_prefix: list[str], **kwargs: t.Any) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(*command_prefix),
            strip_after_prefix=True,
            **kwargs,
        )
        self.db: asyncpg.Pool

    async def setup_db(self) -> None:
        self.db = await asyncpg.create_pool(config("DB_URI"))  # type: ignore

    async def load_cogs(self) -> None:
        cog_extensions = [module.name for module in iter_modules(["cogs"])]
        for extension in cog_extensions:
            await self.load_extension(f"cogs.{extension}")
        await self.load_extension("jishaku")

    async def setup_hook(self) -> None:
        await self.setup_db()
        await self.load_cogs()
        message = f"{self.user} has connected to Discord!"
        logger.info(message)

    async def close(self) -> None:
        await super().close()
        if self.db:
            await self.db.close()


def main() -> None:
    intents = discord.Intents.all()
    activity = discord.Activity(type=discord.ActivityType.listening, name="uwu help")
    bot = Uwuily(
        command_prefix=["uwu", "Uwu"],
        intents=intents,
        application_id=config("APP_ID", cast=int),
        activity=activity,
        case_insensitive=True,
    )
    bot.run(str(config("TOKEN")), reconnect=True)


if __name__ == "__main__":
    main()
