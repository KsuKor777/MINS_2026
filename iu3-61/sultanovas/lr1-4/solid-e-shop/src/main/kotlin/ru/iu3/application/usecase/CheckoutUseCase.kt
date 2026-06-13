package ru.iu3.application.usecase

import ru.iu3.domain.model.Order

internal interface CheckoutUseCase {

    operator fun invoke(userId: String, strategyName: String): Order
}