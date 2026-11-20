"""Мини планировщик на генераторах с create_task и await_task. Условие лежит в README.md.

Постановка: задачи спят через yield from sleep, результата чужой задачи раньше ждать было нечем.
Идея по шагам: первое, ожидание оформлено системным вызовом AwaitTask(tid); второе, планировщик хранит результаты завершенных задач и списки ждущих; третье, ждущая задача паркуется и не планируется, пока цель не завершится; четвертое, финиш цели будит всех ждущих и отдает им результат через send; пятое, ожидание несуществующего tid при пустых очередях дает RuntimeError со словом deadlock.
"""

import time
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

Task = Generator[Any, Any, Any]

# Системные вызовы: единственные объекты, уходящие наружу через yield.


@dataclass
class Sleep:
    duration: float


@dataclass
class AwaitTask:
    tid: int


# Планировщик и глобальный текущий loop.

_current: "Scheduler | None" = None


class Scheduler:
    def __init__(self) -> None:
        # ready хранит кортежи (tid, task, send_value), значение уходит в task.send().
        self.ready: deque[tuple[int, Task, Any]] = deque()
        self.sleeping: list[tuple[float, int, Task]] = []
        self.results: dict[int, Any] = {}
        self.waiters: dict[int, list[tuple[int, Task]]] = {}
        self.next_id = 0

    def _new_tid(self) -> int:
        self.next_id += 1
        return self.next_id

    def create_task(self, coro: Task) -> int:
        tid = self._new_tid()
        self.ready.append((tid, coro, None))
        return tid

    def run(self, main: Task) -> None:
        global _current  # noqa: PLW0603  # аналог asyncio._running_loop
        _current = self
        try:
            self.create_task(main)
            while self._has_work():
                self._wake_sleeping()
                if not self.ready:
                    self._idle_wait_or_deadlock()
                    continue
                self._step_one()
        finally:
            _current = None

    def _has_work(self) -> bool:
        return bool(self.ready or self.sleeping or self.waiters)

    def _wake_sleeping(self) -> None:
        now = time.monotonic()
        still: list[tuple[float, int, Task]] = []
        for wake_at, tid, task in self.sleeping:
            if wake_at <= now:
                self.ready.append((tid, task, None))
            else:
                still.append((wake_at, tid, task))
        self.sleeping = still

    def _idle_wait_or_deadlock(self) -> None:
        if self.sleeping:
            next_wake = min(w for w, _, _ in self.sleeping)
            time.sleep(max(0.0, next_wake - time.monotonic()))
            return
        if self.waiters:
            pending = sorted(self.waiters)
            raise RuntimeError(f"deadlock: задачи {pending} ждут результат, будить их некому")

    def _step_one(self) -> None:
        tid, task, value = self.ready.popleft()
        try:
            syscall = task.send(value)
        except StopIteration as e:
            self._finish_task(tid, e.value)
            return
        self._handle_syscall(tid, task, syscall)

    def _finish_task(self, tid: int, result: Any) -> None:  # noqa: ANN401
        self.results[tid] = result
        for waiter_tid, waiter in self.waiters.pop(tid, []):
            self.ready.append((waiter_tid, waiter, result))

    def _handle_syscall(self, tid: int, task: Task, syscall: Any) -> None:  # noqa: ANN401
        if isinstance(syscall, Sleep):
            self.sleeping.append((time.monotonic() + syscall.duration, tid, task))
        elif isinstance(syscall, AwaitTask):
            if syscall.tid in self.results:
                self.ready.append((tid, task, self.results[syscall.tid]))
            else:
                self.waiters.setdefault(syscall.tid, []).append((tid, task))
        else:
            raise RuntimeError(f"unknown syscall: {syscall!r}")


# Публичный API, повторяет asyncio.


def sleep(duration: float) -> Task:
    """Аналог asyncio.sleep. Вызов в коде задачи: yield from sleep(...)."""
    yield Sleep(duration)


def create_task(coro: Task) -> int:
    """Аналог asyncio.create_task. Регистрирует coro в текущем loop без yield, возвращает tid."""
    if _current is None:
        raise RuntimeError("нет текущего loop, вызывать из main через run()")  # noqa: RUF001
    return _current.create_task(coro)


def await_task(tid: int) -> Task:
    """Ждет завершения задачи tid и возвращает ее результат.

    Вызов в коде задачи: yield from await_task(tid). Планировщик присылает результат через send.
    """
    result = yield AwaitTask(tid)
    return result


def run(main: Task) -> None:
    """Аналог asyncio.run. Создает планировщик и крутит main до завершения."""
    Scheduler().run(main)
