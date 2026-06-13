package ru.iu3.infrastructure.observer

import ru.iu3.domain.model.Order
import ru.iu3.domain.observer.OrderObserver

internal class EmailOrderObserver : OrderObserver {

    override fun onOrderCreated(order: Order) {
        println("[Email] Чек отправлен на почту. Сумма: ${order.totalPrice}")
    }
}

internal class SmsOrderObserver : OrderObserver {

    override fun onOrderCreated(order: Order) {
        println("[SMS] Ваш заказ ${order.id} успешно оформлен!")
    }
}