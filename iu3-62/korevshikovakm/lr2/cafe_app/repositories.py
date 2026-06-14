from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .entities import MenuCategory, MenuItem, Order, OrderLine
from .exceptions import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    ItemNotFoundError,
    OrderAlreadyOpenForTableError,
    OrderClosedError,
    OrderNotFoundError,
)


@dataclass
class InMemoryMenuRepository:
    _categories: dict[int, MenuCategory]
    _items: dict[int, MenuItem]
    _next_category_id: int
    _next_item_id: int

    def __init__(self) -> None:
        self._categories = {}
        self._items = {}
        self._next_category_id = 1
        self._next_item_id = 1

    def add_category(self, name: str) -> MenuCategory:
        name = name.strip()
        if not name:
            raise CategoryNotFoundError("Название категории не может быть пустым.")

        # Уникальность по имени (простая логика для задания).
        for c in self._categories.values():
            if c.name.lower() == name.lower():
                raise CategoryAlreadyExistsError("Такая категория уже существует.")

        cid = self._next_category_id
        self._next_category_id += 1

        category = MenuCategory(id=cid, name=name)
        self._categories[cid] = category
        return category

    def list_categories(self) -> list[MenuCategory]:
        return sorted(self._categories.values(), key=lambda c: c.id)

    def add_item(self, category_id: int, name: str, price: Decimal) -> MenuItem:
        if category_id not in self._categories:
            raise CategoryNotFoundError("Категория не найдена.")

        name = name.strip()
        if not name:
            raise ItemNotFoundError("Название блюда не может быть пустым.")
        if price <= 0:
            raise ItemNotFoundError("Цена должна быть положительной.")

        iid = self._next_item_id
        self._next_item_id += 1

        item = MenuItem(id=iid, category_id=category_id, name=name, price=price)
        self._items[iid] = item
        return item

    def list_items(self, category_id: int | None = None) -> list[MenuItem]:
        items = self._items.values()
        if category_id is not None:
            items = [it for it in items if it.category_id == category_id]
        return sorted(items, key=lambda it: it.id)

    def get_item(self, item_id: int) -> MenuItem:
        try:
            return self._items[item_id]
        except KeyError as e:
            raise ItemNotFoundError("Блюдо не найдено.") from e

    def get_category(self, category_id: int) -> MenuCategory:
        try:
            return self._categories[category_id]
        except KeyError as e:
            raise CategoryNotFoundError("Категория не найдена.") from e


@dataclass
class InMemoryOrderRepository:
    _orders: dict[int, Order]
    _next_order_id: int

    def __init__(self) -> None:
        self._orders = {}
        self._next_order_id = 1

    def create_order(self, table_number: int) -> Order:
        if table_number <= 0:
            raise ValueError("Номер стола должен быть положительным.")

        # Один открытый заказ на стол.
        for o in self._orders.values():
            if o.table_number == table_number and o.status == "OPEN":
                raise OrderAlreadyOpenForTableError("На этот стол уже есть открытый заказ.")

        oid = self._next_order_id
        self._next_order_id += 1
        order = Order(id=oid, table_number=table_number)
        self._orders[oid] = order
        return order

    def get_order(self, order_id: int) -> Order:
        try:
            return self._orders[order_id]
        except KeyError as e:
            raise OrderNotFoundError("Заказ не найден.") from e

    def list_open_orders(self) -> list[Order]:
        return sorted(
            [o for o in self._orders.values() if o.status == "OPEN"],
            key=lambda x: x.id,
        )

    def list_orders_by_table(self, table_number: int) -> list[Order]:
        return sorted(
            [o for o in self._orders.values() if o.table_number == table_number],
            key=lambda x: x.id,
        )

    def get_open_order_by_table(self, table_number: int) -> Order:
        for o in self._orders.values():
            if o.table_number == table_number and o.status == "OPEN":
                return o
        raise OrderNotFoundError("Открытый заказ для этого стола не найден.")

    def add_line(self, order_id: int, line: OrderLine) -> None:
        order = self.get_order(order_id)
        # Order сам проверит статус и выбросит OrderClosedError.
        order.add_line(line)

    def mark_paid(self, order_id: int, payment_method: str, paid_at: datetime) -> None:
        order = self.get_order(order_id)
        if order.status != "OPEN":
            raise OrderClosedError("Заказ уже закрыт.")
        order.status = "CLOSED"
        order.payment_method = payment_method
        order.paid_at = paid_at

