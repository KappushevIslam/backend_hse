from fastapi import APIRouter

from schemas.predict import PredictRequest
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
