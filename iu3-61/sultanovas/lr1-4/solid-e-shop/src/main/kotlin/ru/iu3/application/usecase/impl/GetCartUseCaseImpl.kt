package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.GetCartUseCase
import ru.iu3.domain.model.Cart
import ru.iu3.domain.repository.CartRepository

internal class GetCartUseCaseImpl(
    private val cartRepository: CartRepository,
) : GetCartUseCase {

    override fun invoke(): Cart = cartRepository.get()
}