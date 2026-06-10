from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .exceptions import DuplicateEntityError, EntityNotFoundError
from .models import Booking, Client, Tour
from .notifications import Notification

T = TypeVar("T")


class TourRepository(ABC):
    @abstractmethod
    def add(self, tour: Tour) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, tour_id: int) -> Tour:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Tour]:
        raise NotImplementedError

    @abstractmethod
    def update(self, tour: Tour) -> None:
        raise NotImplementedError


class ClientRepository(ABC):
    @abstractmethod
    def add(self, client: Client) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, client_id: int) -> Client:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Client]:
        raise NotImplementedError


class BookingRepository(ABC):
    @abstractmethod
    def add(self, booking: Booking) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, booking_id: int) -> Booking:
        raise NotImplementedError

    @abstractmethod
    def update(self, booking: Booking) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, booking_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Booking]:
        raise NotImplementedError


class NotificationRepository(ABC):
    @abstractmethod
    def add(self, notification: Notification) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Notification]:
        raise NotImplementedError


class BaseInMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._storage: dict[int, T] = {}

    def _add(self, entity_id: int, entity: T, entity_name: str) -> None:
        if entity_id in self._storage:
            raise DuplicateEntityError(f"{entity_name} с id={entity_id} уже существует")
        self._storage[entity_id] = entity

    def _get(self, entity_id: int, entity_name: str) -> T:
        try:
            return self._storage[entity_id]
        except KeyError as error:
            raise EntityNotFoundError(f"{entity_name} с id={entity_id} не найден") from error

    def _update(self, entity_id: int, entity: T, entity_name: str) -> None:
        if entity_id not in self._storage:
            raise EntityNotFoundError(f"{entity_name} с id={entity_id} не найден")
        self._storage[entity_id] = entity

    def _remove(self, entity_id: int, entity_name: str) -> None:
        if entity_id not in self._storage:
            raise EntityNotFoundError(f"{entity_name} с id={entity_id} не найден")
        del self._storage[entity_id]

    def _list(self) -> list[T]:
        return list(self._storage.values())


class InMemoryTourRepository(BaseInMemoryRepository[Tour], TourRepository):
    def add(self, tour: Tour) -> None:
        self._add(tour.tour_id, tour, "Тур")

    def get_by_id(self, tour_id: int) -> Tour:
        return self._get(tour_id, "Тур")

    def list_all(self) -> list[Tour]:
        return self._list()

    def update(self, tour: Tour) -> None:
        self._update(tour.tour_id, tour, "Тур")


class InMemoryClientRepository(BaseInMemoryRepository[Client], ClientRepository):
    def add(self, client: Client) -> None:
        self._add(client.client_id, client, "Клиент")

    def get_by_id(self, client_id: int) -> Client:
        return self._get(client_id, "Клиент")

    def list_all(self) -> list[Client]:
        return self._list()


class InMemoryBookingRepository(BaseInMemoryRepository[Booking], BookingRepository):
    def add(self, booking: Booking) -> None:
        self._add(booking.booking_id, booking, "Бронирование")

    def get_by_id(self, booking_id: int) -> Booking:
        return self._get(booking_id, "Бронирование")

    def update(self, booking: Booking) -> None:
        self._update(booking.booking_id, booking, "Бронирование")

    def remove(self, booking_id: int) -> None:
        self._remove(booking_id, "Бронирование")

    def list_all(self) -> list[Booking]:
        return self._list()


class InMemoryNotificationRepository(BaseInMemoryRepository[Notification], NotificationRepository):
    def add(self, notification: Notification) -> None:
        self._add(notification.notification_id, notification, "Уведомление")

    def list_all(self) -> list[Notification]:
        return self._list()
