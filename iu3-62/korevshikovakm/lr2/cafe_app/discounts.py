from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from .exceptions import ValidationError


class IDiscountStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def apply(self, amount: Decimal) -> Decimal:
        raise NotImplementedError


class NoDiscountStrategy(IDiscountStrategy):
    @property
    def name(self) -> str:
        return "Без скидки"

    def apply(self, amount: Decimal) -> Decimal:
        return amount


class StudentDiscountStrategy(IDiscountStrategy):
    @property
    def name(self) -> str:
        return "Студенческая скидка 10%"

    def apply(self, amount: Decimal) -> Decimal:
        return amount * Decimal("0.90")


class HappyHourDiscountStrategy(IDiscountStrategy):
    @property
    def name(self) -> str:
        return "Happy hour скидка 15%"

    def apply(self, amount: Decimal) -> Decimal:
        return amount * Decimal("0.85")


@dataclass(frozen=True)
class DiscountResult:
    strategy_name: str
    original_total: Decimal
    discounted_total: Decimal

    @property
    def discount_amount(self) -> Decimal:
        return self.original_total - self.discounted_total


class DiscountFactory:
    def get_strategy(self, key: str) -> IDiscountStrategy:
        normalized = key.strip().lower()
        if normalized in {"none", "без", "0", ""}:
            return NoDiscountStrategy()
        if normalized in {"student", "студент", "1"}:
            return StudentDiscountStrategy()
        if normalized in {"happy", "happyhour", "2"}:
            return HappyHourDiscountStrategy()
        raise ValidationError("Неизвестный тип скидки.")
