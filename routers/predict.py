from fastapi import APIRouter, HTTPException

from exceptions import PredictionError
from repositories.database import get_pool
from repositories.items import ItemRepository
from schemas.predict import PredictRequest, SimplePredictRequest
from services.moderation import ModerationService

router = APIRouter(tags=["predict"])
service = ModerationService()


@router.post(
    "/predict",
    response_model=bool,
    summary="Проверка объявления на нарушения",
    responses={
        400: {"description": "Неверный формат входных данных"},
        500: {"description": "Ошибка на уровне бизнес-логики"},
    },
)
async def predict(payload: PredictRequest) -> bool:
    """Возвращает True, если в объявлении найдено нарушение, иначе False."""
    return service.predict(payload)


@router.post(
    "/simple_predict",
    response_model=bool,
    summary="Проверка объявления на нарушения по идентификатору",
    responses={
        400: {"description": "Неверный формат входных данных"},
        404: {"description": "Объявление не найдено"},
        500: {"description": "Ошибка на уровне бизнес-логики"},
    },
)
async def simple_predict(payload: SimplePredictRequest) -> bool:
    """Догружает объявление и продавца одним запросом и переиспользует predict."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            data = await ItemRepository(conn).get_for_prediction(payload.item_id)
    except Exception as exc:
        raise PredictionError("Не удалось получить данные объявления") from exc
    if data is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return service.predict(PredictRequest(**data))
