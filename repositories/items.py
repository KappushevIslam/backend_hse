import asyncpg


class ItemRepository:
    """Записи таблицы items. Чтение для предсказания идет одним запросом с JOIN."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        seller_id: int,
        name: str,
        description: str,
        category: int,
        images_qty: int,
    ) -> int:
        row = await self._conn.fetchrow(
            "INSERT INTO items (seller_id, name, description, category, images_qty)"
            " VALUES ($1, $2, $3, $4, $5) RETURNING id",
            seller_id,
            name,
            description,
            category,
            images_qty,
        )
        assert row is not None
        return int(row["id"])

    async def get_for_prediction(self, item_id: int) -> dict | None:
        row = await self._conn.fetchrow(
            "SELECT i.id AS item_id, i.seller_id, u.is_verified AS is_verified_seller,"
            " i.name, i.description, i.category, i.images_qty"
            " FROM items i JOIN users u ON u.id = i.seller_id"
            " WHERE i.id = $1",
            item_id,
        )
        return dict(row) if row is not None else None
