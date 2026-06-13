package ru.iu3.application.usecase

import ru.iu3.domain.model.Order

internal interface GetOrderHistoryUseCase {

    operator fun invoke(userId: String): List<Order>
}