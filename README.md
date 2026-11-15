# Сервис проверки объявлений

FastAPI-сервис. `POST /predict` принимает данные объявления и возвращает `true` при нарушении, `false` без нарушения.

Правило первого этапа: подтверждённый продавец нарушений не имеет, неподтверждённый получает `true` при `images_qty = 0`.

| is_verified_seller | images_qty | Ответ |
| --- | --- | --- |
| true | любое | false |
| false | 0 | true |
| false | 1 и больше | false |

Логика по слоям: обработчик в `routers/predict.py`, схема в `schemas/predict.py`, сервис в `services/moderation.py`, порог в `repositories/rules.py`.

## Запуск

```
pip install -r requirements.txt
fastapi dev
```

Документация: http://127.0.0.1:8000/docs.

## Запрос

```bash
curl -X POST http://127.0.0.1:8000/predict -H 'Content-Type: application/json' -d '{
  "seller_id": 1,
  "is_verified_seller": false,
  "item_id": 10,
  "name": "Ноутбук",
  "description": "Рабочий, без царапин",
  "category": 3,
  "images_qty": 0
}'
```

Все семь полей обязательны, числовые значения от 0. Ответ 200 с `true` или `false`, 400 при неверных данных, 500 при ошибке в сервисе или репозитории.

## Тесты

```
pip install -r requirements-dev.txt
pytest
```

Проверяются оба исхода правила, валидация полей и отказ репозитория с ответом 500.

## Ограничение

Правило наивное, модель появится позже. Точка замены: `ModerationService.predict`.
