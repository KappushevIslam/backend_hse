"""Потокобезопасный LRU кеш фиксированной емкости. Условие лежит в README.md.

Постановка: кеш ограниченной емкости вытесняет ключ с самым давним обращением.
Идея по шагам: первое, порядок ключей в OrderedDict отражает давность обращения, самый старый стоит первым; второе, put и успешный get двигают ключ в конец через move_to_end; третье, переполнение чистится через popitem(last=False); четвертое, каждый метод целиком идет под общим RLock, шаги разных потоков не перемешиваются.
"""

from collections import OrderedDict
import threading


class LRUCache[K, V]:
    """Потокобезопасный LRU кеш.

    Инварианты: размер не превышает capacity; при переполнении удаляется ключ с самым давним обращением; успешный get делает ключ самым свежим; put делает ключ самым свежим при вставке и при обновлении.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity должен быть >= 1")
        self._capacity = capacity
        self._data: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.RLock()

    @property
    def capacity(self) -> int:
        return self._capacity

    def put(self, key: K, value: V) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            if len(self._data) > self._capacity:
                self._data.popitem(last=False)

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            if key not in self._data:
                return default
            self._data.move_to_end(key)
            return self._data[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: object) -> bool:
        with self._lock:
            return key in self._data
