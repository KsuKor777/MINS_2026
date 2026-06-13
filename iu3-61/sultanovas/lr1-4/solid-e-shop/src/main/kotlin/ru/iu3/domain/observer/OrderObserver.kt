package ru.iu3.domain.observer

import ru.iu3.domain.model.Order

internal interface OrderObserver {

    fun onOrderCreated(order: Order)
}