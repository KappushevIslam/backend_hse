import pytest
from fastapi.testclient import TestClient

from main import app
from repositories.rules import RuleRepository

VALID_PAYLOAD = {
    "seller_id": 1,
    "is_verified_seller": False,
    "item_id": 10,
    "name": "Ноутбук",
    "description": "Рабочий, без царапин",
    "category": 3,
    "images_qty": 2,
}


def make_payload(**overrides: object) -> dict[str, object]:
    return {**VALID_PAYLOAD, **overrides}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_root_returns_hello_world(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


@pytest.mark.parametrize(
    ("is_verified_seller", "images_qty", "expected"),
    [
        (True, 0, False),
        (True, 10, False),
        (False, 1, False),
        (False, 5, False),
        (False, 0, True),
    ],
    ids=[
        "verified-without-images",
        "verified-with-images",
        "unverified-one-image",
        "unverified-many-images",
        "unverified-without-images",
    ],
)
def test_predict_logic(
    client: TestClient,
    is_verified_seller: bool,
    images_qty: int,
    expected: bool,
) -> None:
    response = client.post(
        "/predict",
        json=make_payload(is_verified_seller=is_verified_seller, images_qty=images_qty),
    )

    assert response.status_code == 200
    assert response.json() is expected


def test_predict_returns_bare_boolean(client: TestClient) -> None:
    response = client.post("/predict", json=make_payload())

    assert response.headers["content-type"] == "application/json"
    assert isinstance(response.json(), bool)


@pytest.mark.parametrize(
    "missing_field",
    list(VALID_PAYLOAD),
)
def test_predict_rejects_missing_field(client: TestClient, missing_field: str) -> None:
    payload = make_payload()
    payload.pop(missing_field)

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"][0]["loc"] == ["body", missing_field]


@pytest.mark.parametrize(
    "invalid_field",
    [
        {"seller_id": "abc"},
        {"item_id": None},
        {"name": ""},
        {"category": "ten"},
        {"images_qty": -1},
        {"is_verified_seller": "maybe"},
    ],
)
def test_predict_rejects_invalid_values(
    client: TestClient, invalid_field: dict[str, object]
) -> None:
    response = client.post("/predict", json=make_payload(**invalid_field))

    assert response.status_code == 400


def test_predict_rejects_empty_body(client: TestClient) -> None:
    response = client.post("/predict", json={})

    assert response.status_code == 400


def test_predict_returns_500_on_repository_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_get_rules(self: RuleRepository) -> None:
        raise RuntimeError("хранилище недоступно")

    monkeypatch.setattr(RuleRepository, "get_rules", broken_get_rules)

    response = client.post("/predict", json=make_payload())

    assert response.status_code == 500
    assert response.json() == {"detail": "Не удалось загрузить правила модерации"}
