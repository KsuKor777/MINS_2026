package ru.iu3.application.usecase.impl

import ru.iu3.application.generator.IdGenerator
import ru.iu3.application.usecase.CheckoutUseCase
import ru.iu3.domain.exception.EmptyCartException
import ru.iu3.domain.factory.PaymentStrategyFactory
import ru.iu3.domain.model.Order
import ru.iu3.domain.observer.OrderEventPublisher
import ru.iu3.domain.repository.CartRepository
import ru.iu3.domain.repository.OrderRepository

internal class CheckoutUseCaseImpl(
    private val cartRepository: CartRepository,
    private val orderRepository: OrderRepository,
    private val idGenerator: IdGenerator,
    private val eventPublisher: OrderEventPublisher,
    private val strategyFactory: PaymentStrategyFactory,
) : CheckoutUseCase {

    override fun invoke(userId: String, strategyName: String): Order {
        val cart = cartRepository.get()
        if (cart.isEmpty()) throw EmptyCartException()

        val strategy = strategyFactory.getByTitle(strategyName)
        val items = cart.getItems()
        val totalPrice = cart.getTotalPrice()

        val status = strategy.pay(totalPrice)

        val order = Order(
            id = idGenerator.newId(),
            userId = userId,
            status = status,
            totalPrice = totalPrice,
            paymentMethod = strategy.name,
            items = items,
        )

        orderRepository.save(order)
        eventPublisher.notifyOrderCreated(order)
        cartRepository.clear()

        return order
    }
}