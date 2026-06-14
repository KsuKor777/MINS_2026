from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .entities import Order
from .payment import PaymentResult
from .utils import format_money


@dataclass(frozen=True)
class Receipt:
    order_id: int
    table_number: int
    created_at: datetime
    payment_method: str
    confirmation: str
    subtotal: Decimal
    total: Decimal

    def render(self) -> str:
        lines: list[str] = []
        lines.append("====================================")
        lines.append("ЧЕК")
        lines.append(f"Заказ №: {self.order_id}")
        lines.append(f"Стол: {self.table_number}")
        lines.append(f"Дата: {self.created_at:%Y-%m-%d %H:%M:%S}")
        lines.append("------------------------------------")

        # Строки товаров берём из заказа при генерации.
        # Здесь оставляем место под отображение.
        lines.append("(состав заказа отображается в тексте чека)")
        lines.append("------------------------------------")

        lines.append(f"Оплата: {self.payment_method}")
        lines.append(f"Подтверждение: {self.confirmation}")
        lines.append("------------------------------------")
        lines.append(f"Итого: {format_money(self.total)}")
        lines.append("====================================")
        return "\n".join(lines)


class ReceiptService:
    def generate_receipt_text(
        self,
        order: Order,
        payment: PaymentResult,
        original_total: Decimal,
        discounted_total: Decimal,
        discount_name: str,
    ) -> str:
        created_at = datetime.now()
        subtotal = original_total

        lines: list[str] = []
        lines.append("====================================")
        lines.append("ЧЕК")
        lines.append(f"Заказ №: {order.id}")
        lines.append(f"Стол: {order.table_number}")
        lines.append(f"Дата: {created_at:%Y-%m-%d %H:%M:%S}")
        lines.append("------------------------------------")
        for ln in order.lines:
            line_total = ln.line_total
            lines.append(f"{ln.quantity} x {ln.item_name} @ {format_money(ln.unit_price)} = {format_money(line_total)}")

        lines.append("------------------------------------")
        lines.append(f"Подитог: {format_money(subtotal)}")
        lines.append(f"Скидка: {discount_name}")
        lines.append(f"Сумма скидки: {format_money(subtotal - discounted_total)}")
        lines.append(f"Оплата: {payment.method_name}")
        lines.append(f"Подтверждение: {payment.confirmation}")
        lines.append(f"Итого: {format_money(discounted_total)}")
        lines.append("====================================")
        return "\n".join(lines)

