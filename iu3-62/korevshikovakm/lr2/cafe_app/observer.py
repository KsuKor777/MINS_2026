from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .entities import Order


class IOrderObserver(ABC):
    @abstractmethod
    def update(self, event_name: str, order: Order) -> None:
        raise NotImplementedError


@dataclass
class OrderEventPublisher:
    _observers: list[IOrderObserver] = field(default_factory=list)

    def subscribe(self, observer: IOrderObserver) -> None:
        self._observers.append(observer)

    def notify(self, event_name: str, order: Order) -> None:
        for observer in self._observers:
            observer.update(event_name, order)


@dataclass
class InMemoryOrderLogObserver(IOrderObserver):
    events: list[str] = field(default_factory=list)

    def update(self, event_name: str, order: Order) -> None:
        self.events.append(f"{event_name}: order={order.id}, table={order.table_number}, status={order.status}")
