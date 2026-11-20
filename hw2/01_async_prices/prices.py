"""Сравнение цен в магазинах через asyncio. Условие лежит в README.md."""

import asyncio

# База магазинов: цена и время ответа API в секундах. НЕ менять.
PRICES: dict[str, int] = {"ozon": 990, "wb": 950, "yandex": 1100, "slow_shop": 900}
DELAYS: dict[str, float] = {"ozon": 0.3, "wb": 0.2, "yandex": 0.4, "slow_shop": 5.0}


async def fetch_price(shop: str) -> int:
    """Имитирует запрос к API магазина. НЕ менять.

    Неизвестный магазин отвечает за 0.1 с и возвращает цену 1000.
    """
    await asyncio.sleep(DELAYS.get(shop, 0.1))
    return PRICES.get(shop, 1000)


async def get_prices_sequential(shops: list[str]) -> list[int]:
    """Собирает цены по очереди.

    Шаг 1: цикл идет по магазинам в заданном порядке.
    Шаг 2: каждый fetch_price ожидается до конца, следующий запрос стартует после.
    Итоговое время равно сумме задержек.
    """
    prices: list[int] = []
    for shop in shops:
        prices.append(await fetch_price(shop))
    return prices


async def get_prices_concurrent(shops: list[str]) -> list[int]:
    """Собирает цены одновременно.

    Шаг 1: gather запускает все запросы сразу.
    Шаг 2: gather возвращает результаты в порядке магазинов.
    Итоговое время равно самой долгой задержке.
    """
    return list(await asyncio.gather(*(fetch_price(shop) for shop in shops)))


async def get_price_or_none(shop: str, timeout: float = 1.0) -> int | None:
    """Возвращает цену магазина.

    Шаг 1: ждет ответ через wait_for с лимитом timeout.
    Шаг 2: при истечении лимита wait_for бросает TimeoutError, возвращается None.
    """
    try:
        return await asyncio.wait_for(fetch_price(shop), timeout=timeout)
    except TimeoutError:
        return None


async def get_prices_with_timeout(shops: list[str], timeout: float = 1.0) -> list[int | None]:
    """Повторяет get_prices_concurrent.

    Медленные магазины дают None и не задерживают остальных.
    """
    return list(await asyncio.gather(*(get_price_or_none(shop, timeout) for shop in shops)))


async def get_prices_limited(shops: list[str], limit: int = 3) -> list[int]:
    """Собирает цены одновременно с лимитом на параллельность.

    Шаг 1: семафор пропускает не больше limit запросов сразу.
    Шаг 2: вспомогательная корутина берет семафор через async with и зовет fetch_price.
    Шаг 3: gather собирает результаты в порядке магазинов.
    """
    sem = asyncio.Semaphore(limit)

    async def one(shop: str) -> int:
        async with sem:
            return await fetch_price(shop)

    return list(await asyncio.gather(*(one(shop) for shop in shops)))


if __name__ == "__main__":
    import time

    async def main() -> None:
        shops = ["ozon", "wb", "yandex"]
        for fn in (get_prices_sequential, get_prices_concurrent):
            start = time.perf_counter()
            result = await fn(shops)
            print(f"{fn.__name__:25} {time.perf_counter() - start:.2f}s  {result}")

        start = time.perf_counter()
        result_with_timeout = await get_prices_with_timeout(shops + ["slow_shop"])
        print(f"{'get_prices_with_timeout':25} {time.perf_counter() - start:.2f}s  {result_with_timeout}")

    asyncio.run(main())
