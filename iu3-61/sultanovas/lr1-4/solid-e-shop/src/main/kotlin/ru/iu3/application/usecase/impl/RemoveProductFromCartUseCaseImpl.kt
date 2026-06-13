package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.RemoveProductFromCartUseCase
import ru.iu3.domain.exception.InvalidAmountException
import ru.iu3.domain.exception.ProductNotFoundException
import ru.iu3.domain.repository.CartRepository
import ru.iu3.domain.repository.ProductRepository

internal class RemoveProductFromCartUseCaseImpl(
    private val productRepository: ProductRepository,
    private val cartRepository: CartRepository,
) : RemoveProductFromCartUseCase {

    override fun invoke(productId: String, amount: Int) {
        if (amount <= 0) throw InvalidAmountException()

        val product = productRepository.findById(productId)
            ?: throw ProductNotFoundException(productId)

        val cart = cartRepository.get()
        cart.remove(product, amount)
    }
}