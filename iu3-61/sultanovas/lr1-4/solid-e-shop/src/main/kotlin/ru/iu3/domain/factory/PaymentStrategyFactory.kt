package ru.iu3.domain.factory

import ru.iu3.domain.strategy.PaymentStrategy

internal interface PaymentStrategyFactory {

    fun getAll(): List<PaymentStrategy>

    fun getByTitle(title: String): PaymentStrategy
}