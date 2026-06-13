package ru.iu3.application.usecase

internal interface AddProductToCartUseCase {

    operator fun invoke(productId: String, amount: Int = 1)
}