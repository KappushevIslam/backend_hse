from dataclasses import dataclass


@dataclass(frozen=True)
class ModerationRules:
    min_images_for_unverified: int


class RuleRepository:
    """Хранилище правил модерации.

    Данные лежат в памяти. При переходе на БД меняется только реализация метода,
    интерфейс сервиса остаётся прежним.
    """

    def __init__(self) -> None:
        self._rules = ModerationRules(min_images_for_unverified=1)

    def get_rules(self) -> ModerationRules:
        return self._rules
