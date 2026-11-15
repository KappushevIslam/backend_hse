from loguru import logger

from exceptions import PredictionError
from repositories.rules import RuleRepository
from schemas.predict import PredictRequest


class ModerationService:
    """Наивная проверка объявления на нарушения.

    Шаг 1: читаем правила из репозитория.
    Шаг 2: подтверждённый продавец получает False, нарушений нет.
    Шаг 3: неподтверждённый продавец получает True, если изображений меньше порога.
    """

    def __init__(self, rules_repository: RuleRepository | None = None) -> None:
        self._rules_repository = rules_repository or RuleRepository()

    def predict(self, payload: PredictRequest) -> bool:
        try:
            rules = self._rules_repository.get_rules()
        except Exception as exc:
            raise PredictionError("Не удалось загрузить правила модерации") from exc

        is_violation = (
            not payload.is_verified_seller
            and payload.images_qty < rules.min_images_for_unverified
        )
        logger.bind(seller_id=payload.seller_id, item_id=payload.item_id).info(
            "prediction: violation={}", is_violation
        )
        return is_violation
