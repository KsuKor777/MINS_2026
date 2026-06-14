from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from .exceptions import PaymentError, PaymentMethodNotSupportedError


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    method_name: str
    confirmation: str


class IPaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: Decimal) -> PaymentResult:
        raise NotImplementedError


class CashPaymentProcessor(IPaymentProcessor):
    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            raise PaymentError("Сумма к оплате должна быть больше нуля.")
        return PaymentResult(ok=True, method_name="Наличные", confirmation=str(uuid4()))


class CardPaymentProcessor(IPaymentProcessor):
    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            raise PaymentError("Сумма к оплате должна быть больше нуля.")
        return PaymentResult(ok=True, method_name="Карта", confirmation=str(uuid4()))


class OnlinePaymentProcessor(IPaymentProcessor):
    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            raise PaymentError("Сумма к оплате должна быть больше нуля.")
        return PaymentResult(ok=True, method_name="Онлайн", confirmation=str(uuid4()))


class PaymentFactory:
    def get_processor(self, method_key: str) -> IPaymentProcessor:
        key = method_key.strip().lower()
        if key in {"cash", "наличные", "н"}:
            return CashPaymentProcessor()
        if key in {"card", "карта", "к"}:
            return CardPaymentProcessor()
        if key in {"online", "онлайн", "o"}:
            return OnlinePaymentProcessor()
        raise PaymentMethodNotSupportedError("Способ оплаты не поддерживается.")

