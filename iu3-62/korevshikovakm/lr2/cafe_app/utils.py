from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_money(text: str) -> Decimal:
    raw = text.strip().replace(",", ".")
    try:
        value = Decimal(raw)
    except InvalidOperation as e:
        raise ValueError("Некорректный формат числа.") from e
    return value


def format_money(amount: Decimal) -> str:
    #делаем фиксированный формат.
    return f"{amount:.2f}"

