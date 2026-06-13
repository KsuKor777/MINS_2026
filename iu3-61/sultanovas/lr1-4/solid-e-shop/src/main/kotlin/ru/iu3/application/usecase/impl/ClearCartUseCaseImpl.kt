package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.ClearCartUseCase
import ru.iu3.domain.repository.CartRepository

internal class ClearCartUseCaseImpl(
    private val cartRepository: CartRepository,
) : ClearCartUseCase {

    override fun invoke() {
        cartRepository.clear()
    }
}