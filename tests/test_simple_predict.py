import asyncio
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient

from main import app
from repositories.items import ItemRepository
from repositories.users import UserRepository

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5435/hw")


def run(coro):
    return asyncio.run(coro)


async def _reseed() -> dict[str, int]:
    conn = await asyncpg.connect(DSN)
    try:
        await conn.execute("TRUNCATE items, users RESTART IDENTITY CASCADE")
        users = UserRepository(conn)
        items = ItemRepository(conn)
        verified = await users.create("Иван", "Петров", True)
        unverified = await users.create("Петр", "Иванов", False)
        bad = await items.create(unverified, "Ноутбук", "Без фото", 3, 0)
        good_images = await items.create(unverified, "Стул", "С фото", 3, 2)
        good_verified = await items.create(verified, "Стол", "Без фото", 3, 0)
        return {
            "verified": verified,
            "unverified": unverified,
            "bad": bad,
            "good_images": good_images,
            "good_verified": good_verified,
        }
    finally:
        await conn.close()


@pytest.fixture()
def ids() -> dict[str, int]:
    return run(_reseed())


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_simple_predict_true(client: TestClient, ids: dict[str, int]) -> None:
    response = client.post("/simple_predict", json={"item_id": ids["bad"]})

    assert response.status_code == 200
    assert response.json() is True


def test_simple_predict_false_with_images(client: TestClient, ids: dict[str, int]) -> None:
    response = client.post("/simple_predict", json={"item_id": ids["good_images"]})

    assert response.status_code == 200
    assert response.json() is False


def test_simple_predict_false_verified(client: TestClient, ids: dict[str, int]) -> None:
    response = client.post("/simple_predict", json={"item_id": ids["good_verified"]})

    assert response.status_code == 200
    assert response.json() is False


def test_simple_predict_returns_bare_boolean(client: TestClient, ids: dict[str, int]) -> None:
    response = client.post("/simple_predict", json={"item_id": ids["bad"]})

    assert response.headers["content-type"] == "application/json"
    assert isinstance(response.json(), bool)


def test_simple_predict_404_for_missing_item(client: TestClient, ids: dict[str, int]) -> None:
    response = client.post("/simple_predict", json={"item_id": 999999})

    assert response.status_code == 404
    assert response.json() == {"detail": "Объявление не найдено"}


@pytest.mark.parametrize("bad_body", [{"item_id": -1}, {"item_id": "abc"}, {}])
def test_simple_predict_400_for_invalid_input(
    client: TestClient, ids: dict[str, int], bad_body: dict
) -> None:
    response = client.post("/simple_predict", json=bad_body)

    assert response.status_code == 400


async def _create_and_read() -> dict:
    conn = await asyncpg.connect(DSN)
    try:
        user_id = await UserRepository(conn).create("Анна", "Сидорова", False, 1)
        user = await UserRepository(conn).get_by_id(user_id)
        assert user is not None
        assert user["first_name"] == "Анна"
        assert user["violations_qty"] == 1
        item_id = await ItemRepository(conn).create(user_id, "Лампа", "Яркая", 5, 0)
        data = await ItemRepository(conn).get_for_prediction(item_id)
        assert data is not None
        return data
    finally:
        await conn.close()


def test_repositories_create_and_read(ids: dict[str, int]) -> None:
    data = run(_create_and_read())

    assert data["is_verified_seller"] is False
    assert data["name"] == "Лампа"
    assert data["images_qty"] == 0


async def _read_missing() -> None:
    conn = await asyncpg.connect(DSN)
    try:
        assert await UserRepository(conn).get_by_id(999999) is None
        assert await ItemRepository(conn).get_for_prediction(999999) is None
    finally:
        await conn.close()


def test_repositories_return_none_for_missing(ids: dict[str, int]) -> None:
    run(_read_missing())
