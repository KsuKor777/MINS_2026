package ru.iu3.application.usecase

import ru.iu3.domain.model.Cart

internal interface GetCartUseCase {

    operator fun invoke(): Cart
}