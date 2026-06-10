from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from .exceptions import UnitOfWorkError

RollbackAction = Callable[[], None]


class UnitOfWork(ABC):
    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        raise NotImplementedError

    @abstractmethod
    def register_rollback(self, action: RollbackAction) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._rollback_actions: list[RollbackAction] = []
        self._committed = False

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._rollback_actions = []
        self._committed = False
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is not None or not self._committed:
            self.rollback()
        return False

    def register_rollback(self, action: RollbackAction) -> None:
        self._rollback_actions.append(action)

    def commit(self) -> None:
        self._committed = True
        self._rollback_actions.clear()

    def rollback(self) -> None:
        errors: list[Exception] = []
        for action in reversed(self._rollback_actions):
            try:
                action()
            except Exception as error:  
                errors.append(error)

        self._rollback_actions.clear()
        if errors:
            raise UnitOfWorkError("Не удалось корректно выполнить возврат") from errors[0]
