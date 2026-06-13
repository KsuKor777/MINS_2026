package ru.iu3.infrastructure.strategy

import ru.iu3.domain.exception.InsufficientBonusesException
import ru.iu3.domain.exception.InvalidAmountException
import ru.iu3.domain.model.OrderStatus

internal abstract class PaymentStrategy : ru.iu3.domain.strategy.PaymentStrategy {

    override fun pay(price: Double): OrderStatus {
        if (price <= 0) throw InvalidAmountException()
        return OrderStatus.SUCCESS
    }
}

internal class CardPaymentStrategy : PaymentStrategy() {

    override val name: String = "Карта"
}

internal class CashPaymentStrategy : PaymentStrategy() {

    override val name: String = "Наличные"
}

internal class BonusPaymentStrategy(
    private val availableBonuses: Double = 50000.0,
) : PaymentStrategy() {

    override val name: String = "Бонусы"

    override fun pay(price: Double): OrderStatus {
        if (price > availableBonuses) throw InsufficientBonusesException()
        return super.pay(price)
    }
}