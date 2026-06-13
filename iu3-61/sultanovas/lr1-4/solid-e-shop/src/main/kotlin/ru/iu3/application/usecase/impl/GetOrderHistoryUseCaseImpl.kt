package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.GetOrderHistoryUseCase
import ru.iu3.domain.model.Order
import ru.iu3.domain.repository.OrderRepository

internal class GetOrderHistoryUseCaseImpl(
    private val orderRepository: OrderRepository,
) : GetOrderHistoryUseCase {

    override fun invoke(userId: String): List<Order> = orderRepository.findByUserId(userId)
}