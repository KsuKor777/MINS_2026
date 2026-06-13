package ru.iu3.infrastructure.factory

import ru.iu3.domain.exception.PaymentMethodNotFoundException
import ru.iu3.domain.factory.PaymentStrategyFactory
import ru.iu3.domain.strategy.PaymentStrategy

internal class PaymentStrategyFactoryImpl(
    strategies: List<PaymentStrategy>
) : PaymentStrategyFactory {

    private val strategyMap = strategies.associateBy { it.name }

    override fun getAll(): List<PaymentStrategy> {
        return strategyMap.values.toList()
    }

    override fun getByTitle(title: String): PaymentStrategy {
        return strategyMap[title] ?: throw PaymentMethodNotFoundException()
    }
}