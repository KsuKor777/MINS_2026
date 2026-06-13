package ru.iu3.application.usecase

import ru.iu3.domain.model.Product

internal interface GetAllProductsUseCase {

    operator fun invoke(): List<Product>
}