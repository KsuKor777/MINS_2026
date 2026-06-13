package ru.iu3.domain.exception

open class NotFoundException(message: String) : ShopException(message)

class ProductNotFoundException(productId: String) : NotFoundException("No product with id: $productId")
class OrderNotFoundException(orderId: String) : NotFoundException("No such order")
class PaymentMethodNotFoundException : NotFoundException("No such payment method")