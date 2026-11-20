from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Входные данные объявления.

    Все поля обязательные. Числовые поля ограничены снизу нулём:
    отрицательный идентификатор или количество изображений не имеют смысла.
    """

    seller_id: int = Field(ge=0, examples=[1])
    is_verified_seller: bool = Field(examples=[False])
    item_id: int = Field(ge=0, examples=[10])
    name: str = Field(min_length=1, max_length=256, examples=["Ноутбук"])
    description: str = Field(max_length=5000, examples=["Рабочий, без царапин"])
    category: int = Field(ge=0, examples=[3])
    images_qty: int = Field(ge=0, examples=[2])


class SimplePredictRequest(BaseModel):
    """Вход ручки simple_predict. По идентификатору данные догружаются из БД."""

    item_id: int = Field(ge=0, examples=[10])
