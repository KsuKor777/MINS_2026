package ru.iu3.domain.observer

import ru.iu3.domain.model.Order

internal class OrderEventPublisher {

    private val observers = mutableListOf<OrderObserver>()

    fun subscribe(observer: OrderObserver) {
        observers.add(observer)
    }

    fun unsubscribe(observer: OrderObserver) {
        observers.remove(observer)
    }

    fun notifyOrderCreated(order: Order) {
        observers.forEach { it.onOrderCreated(order) }
    }
}