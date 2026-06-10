from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from .exceptions import ValidationError


@dataclass(slots=True)
class Notification:
    notification_id: int
    event_type: str
    message: str
    created_at: datetime
    booking_id: int | None = None

    def __post_init__(self) -> None:
        if self.notification_id <= 0:
            raise ValidationError("Идентификатор уведомления должен быть положительным")
        if not self.event_type.strip():
            raise ValidationError("Тип уведомления не должен быть пустым")
        if not self.message.strip():
            raise ValidationError("Текст уведомления не должен быть пустым")


@dataclass(slots=True)
class NotificationEvent:
    event_type: str
    message: str
    booking_id: int | None = None

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValidationError("Тип события не должен быть пустым")
        if not self.message.strip():
            raise ValidationError("Текст события не должен быть пустым")


class NotificationObserver(ABC):
    @abstractmethod
    def update(self, event: NotificationEvent) -> None:
        raise NotImplementedError


class NotificationPublisher:
    def __init__(self) -> None:
        self._observers: list[NotificationObserver] = []

    def attach(self, observer: NotificationObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: NotificationObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: NotificationEvent) -> None:
        for observer in self._observers:
            observer.update(event)


class NotificationLogObserver(NotificationObserver):
    def __init__(
        self,
        repository,
        id_generator,
    ) -> None:
        self._repository = repository
        self._id_generator = id_generator

    def update(self, event: NotificationEvent) -> None:
        notification = Notification(
            notification_id=self._id_generator.next_id(),
            event_type=event.event_type,
            message=event.message,
            created_at=datetime.now(),
            booking_id=event.booking_id,
        )
        self._repository.add(notification)


class NotificationStatsObserver(NotificationObserver):
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()

    def update(self, event: NotificationEvent) -> None:
        self._counts[event.event_type] += 1

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)
