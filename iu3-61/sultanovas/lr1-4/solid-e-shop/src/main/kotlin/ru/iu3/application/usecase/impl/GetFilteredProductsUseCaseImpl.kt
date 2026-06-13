package ru.iu3.application.usecase.impl

import ru.iu3.application.usecase.GetFilteredProductsUseCase
import ru.iu3.domain.model.Product
import ru.iu3.domain.model.ProductFilter
import ru.iu3.domain.repository.ProductRepository

internal class GetFilteredProductsUseCaseImpl(
    private val productRepository: ProductRepository,
) : GetFilteredProductsUseCase {

    override fun invoke(filter: ProductFilter): List<Product> =
        productRepository.findByFilter(filter)
}