package ru.iu3.application.usecase

internal interface RemoveProductFromCartUseCase {

    operator fun invoke(productId: String, amount: Int = 1)
}