package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.AddProductToCartUseCase
import ru.iu3.domain.exception.InvalidAmountException
import ru.iu3.domain.exception.ProductNotFoundException
import ru.iu3.domain.repository.CartRepository
import ru.iu3.domain.repository.ProductRepository

internal class AddProductToCartUseCaseImpl(
    private val productRepository: ProductRepository,
    private val cartRepository: CartRepository,
) : AddProductToCartUseCase {

    override fun invoke(productId: String, amount: Int) {
        if (amount <= 0) throw InvalidAmountException()

        val product = productRepository.findById(productId) ?: throw ProductNotFoundException(productId)

        val cart = cartRepository.get()
        cart.add(product, amount)
    }
}