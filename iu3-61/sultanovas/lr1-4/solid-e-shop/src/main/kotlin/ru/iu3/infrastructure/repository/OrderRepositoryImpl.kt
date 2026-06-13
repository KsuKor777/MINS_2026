package ru.iu3.infrastructure.repository

import ru.iu3.domain.model.Order
import ru.iu3.domain.repository.OrderRepository

internal class OrderRepositoryImpl(
    initialOrders: List<Order> = emptyList(),
) : OrderRepository {

    private val ordersById: MutableMap<String, Order> =
        initialOrders.associateBy { it.id }.toMutableMap()

    override fun save(order: Order) {
        ordersById[order.id] = order
    }

    override fun findByUserId(userId: String): List<Order> =
        ordersById.values.filter { it.userId == userId }

    override fun findById(orderId: String): Order? = ordersById[orderId]
}