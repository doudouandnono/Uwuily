import typing as t
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from discord.ext import commands

from models.anicard import Anicard

if t.TYPE_CHECKING:
    import asyncpg


@dataclass
class User:
    user_id: int | None = None
    cooldowns: dict = field(default_factory=dict)
    configs: dict = field(default_factory=dict)
    anicards: list = field(default_factory=list)
    minions: list = field(default_factory=list)

    async def register(self, ctx: commands.Context) -> None:
        fake_datetime = datetime.utcnow() - timedelta(days=30)
        async with ctx.bot.db.acquire() as connection, connection.transaction():
            await connection.execute(
                """
                    INSERT INTO users (user_id)
                    VALUES ($1)
                    ON CONFLICT DO NOTHING;
                """,
                ctx.author.id,
            )
            await connection.execute(
                """
                    INSERT INTO user_configs (user_id)
                    VALUES ($1)
                    ON CONFLICT DO NOTHING;
                """,
                ctx.author.id,
            )
            await connection.execute(
                """
                    INSERT INTO user_stats (user_id)
                    VALUES ($1)
                    ON CONFLICT DO NOTHING;
                """,
                ctx.author.id,
            )
            await connection.execute(
                """
                    INSERT INTO user_skills (user_id, skill_name, skill_level, skill_xp)
                    VALUES
                        ($1, 'Agility', 1, 0),
                        ($1, 'Cooking', 1, 0),
                        ($1, 'Fishing', 1, 0);
                """,
                ctx.author.id,
            )
            await connection.execute(
                """
                    INSERT INTO user_cooldowns (user_id, membership_expire_ts, last_wish_ts, last_weeble_ts)
                    VALUES ($1, $2, $2, $2);
                """,
                ctx.author.id,
                fake_datetime,
            )

    async def fetch_data(
        self,
        ctx: commands.Context,
        get_cooldowns: bool = False,
        get_configs: bool = False,
        get_anicards: bool = False,
        get_minions: bool = False,
    ) -> None:
        if get_cooldowns:
            query: asyncpg.Record = await ctx.bot.db.fetchrow(
                """
                    SELECT *
                    FROM user_cooldowns
                    WHERE user_id = $1;
                """,
                ctx.author.id,
            )
            cooldown_data = dict(query) if query else {}
            self.cooldowns = cooldown_data

        if get_configs:
            query: asyncpg.Record = await ctx.bot.db.fetchrow(
                """
                SELECT *
                FROM user_configs
                WHERE user_id = $1;
                """,
                ctx.author.id,
            )
            config_data = dict(query) if query else {}
            self.configs = config_data

        if get_anicards:
            query: asyncpg.Record = await ctx.bot.db.fetch(
                """
                SELECT *
                FROM user_anicards
                JOIN minions ON user_anicards.minion_id = minions.minion_id
                WHERE user_id = $1;
                """,
                ctx.author.id,
            )
            anicard_data = [dict(record) for record in query]
            self.anicards = [Anicard(**item) for item in anicard_data]

        if get_minions:
            pass
