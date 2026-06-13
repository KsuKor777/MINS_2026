package ru.iu3.domain.repository

import ru.iu3.domain.model.Order

internal interface OrderRepository {

    fun save(order: Order)

    fun findByUserId(userId: String): List<Order>

    fun findById(orderId: String): Order?
}