from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MenuCategory:
    id: int
    name: str


@dataclass(frozen=True)
class MenuItem:
    id: int
    category_id: int
    name: str
    price: Decimal


@dataclass
class OrderLine:
    item_id: int
    item_name: str
    unit_price: Decimal
    quantity: int

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)


@dataclass
class Order:
    id: int
    table_number: int
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "OPEN"
    lines: list[OrderLine] = field(default_factory=list)
    paid_at: datetime | None = None
    payment_method: str | None = None

    def add_line(self, line: OrderLine) -> None:
        self._assert_open()
        self.lines.append(line)

    def _assert_open(self) -> None:
        if self.status != "OPEN":
            # Это отдельная ветка для демонстрации обработки ошибок.
            from .exceptions import OrderClosedError

            raise OrderClosedError("Заказ уже закрыт.")

    def total_amount(self) -> Decimal:
        return sum((ln.line_total for ln in self.lines), Decimal("0.00"))

