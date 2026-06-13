package ru.iu3.application.usecase

import ru.iu3.domain.model.Product
import ru.iu3.domain.model.ProductFilter

internal interface GetFilteredProductsUseCase {

    operator fun invoke(filter: ProductFilter): List<Product>
}