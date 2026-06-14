from __future__ import annotations


class CafeError(Exception):
    """Базовый класс для всех ошибок системы кафе."""


class ValidationError(CafeError):
    """Ошибка валидации пользовательского ввода или данных."""


class NotFoundError(CafeError):
    """Ресурс не найден (категория/блюдо/заказ)."""


class PaymentError(CafeError):
    """Ошибка, связанная с оплатой."""


class MenuError(CafeError):
    """Ошибки, связанные с меню."""


class CategoryAlreadyExistsError(ValidationError):
    pass


class CategoryNotFoundError(NotFoundError):
    pass


class ItemNotFoundError(NotFoundError):
    pass


class OrderError(CafeError):
    """Ошибки, связанные с оформлением заказов."""


class OrderNotFoundError(NotFoundError):
    pass


class OrderAlreadyOpenForTableError(OrderError):
    pass


class OrderClosedError(OrderError):
    pass


class PaymentMethodNotSupportedError(PaymentError):
    pass

