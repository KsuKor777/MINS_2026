package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.GetAllProductsUseCase
import ru.iu3.domain.model.Product
import ru.iu3.domain.repository.ProductRepository

internal class GetAllProductsUseCaseImpl(
    private val productRepository: ProductRepository,
) : GetAllProductsUseCase {

    override fun invoke(): List<Product> = productRepository.findAll()
}