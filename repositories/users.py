import asyncpg


class UserRepository:
    """Записи таблицы users. Соединение приходит снаружи, пулом владеет вызывающий код."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        first_name: str,
        last_name: str,
        is_verified: bool,
        violations_qty: int = 0,
    ) -> int:
        row = await self._conn.fetchrow(
            "INSERT INTO users (first_name, last_name, is_verified, violations_qty)"
            " VALUES ($1, $2, $3, $4) RETURNING id",
            first_name,
            last_name,
            is_verified,
            violations_qty,
        )
        assert row is not None
        return int(row["id"])

    async def get_by_id(self, user_id: int) -> asyncpg.Record | None:
        return await self._conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
