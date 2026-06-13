package ru.iu3.domain.exception

open class ValidationException(message: String) : ShopException(message)

class InvalidAmountException : ValidationException("Amount is invalid")
class EmptyCartException : ValidationException("Cart is empty")
class InvalidFilterException : ValidationException("Wrong filter")
class InsufficientBonusesException : ValidationException("Not enough bonuses")