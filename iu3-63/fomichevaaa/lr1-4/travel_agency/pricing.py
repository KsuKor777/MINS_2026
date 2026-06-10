from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from .exceptions import PricingError, ValidationError
from .models import Client, Tour, to_money


class DiscountPolicy(ABC):
    @abstractmethod
    def get_discount_rate(self, client: Client, tour: Tour, travelers_count: int) -> Decimal:
        raise NotImplementedError


class LoyaltyDiscountPolicy(DiscountPolicy):
    _discounts = {
        "standard": Decimal("0.00"),
        "silver": Decimal("0.05"),
        "gold": Decimal("0.10"),
    }

    def get_discount_rate(self, client: Client, tour: Tour, travelers_count: int) -> Decimal:
        del tour
        del travelers_count
        return self._discounts[client.loyalty_level]


class GroupDiscountPolicy(DiscountPolicy):
    def get_discount_rate(self, client: Client, tour: Tour, travelers_count: int) -> Decimal:
        del client
        del tour
        if travelers_count >= 4:
            return Decimal("0.07")
        if travelers_count >= 2:
            return Decimal("0.03")
        return Decimal("0.00")


class CompositeDiscountPolicy(DiscountPolicy):
    def __init__(self, policies: list[DiscountPolicy], max_discount: Decimal = Decimal("0.20")) -> None:
        self._policies = policies
        self._max_discount = max_discount

    def get_discount_rate(self, client: Client, tour: Tour, travelers_count: int) -> Decimal:
        total_discount = sum(
            policy.get_discount_rate(client, tour, travelers_count) for policy in self._policies
        )
        if total_discount < Decimal("0"):
            raise PricingError("Суммарная скидка не может быть отрицательной")
        return min(total_discount, self._max_discount)


class PriceCalculator:
    def __init__(self, discount_policy: DiscountPolicy) -> None:
        self._discount_policy = discount_policy

    def calculate(self, tour: Tour, client: Client, travelers_count: int) -> tuple[Decimal, Decimal]:
        if travelers_count <= 0:
            raise ValidationError("Количество путешественников должно быть больше нуля")

        base_total = tour.base_price * travelers_count
        discount_rate = self._discount_policy.get_discount_rate(client, tour, travelers_count)

        if not Decimal("0") <= discount_rate <= Decimal("1"):
            raise PricingError("Итоговая скидка должна быть в диапазоне от 0 до 1")

        final_price = to_money(base_total * (Decimal("1") - discount_rate))
        return final_price, discount_rate

