package ru.iu3.presentation.console

import ru.iu3.application.usecase.*
import ru.iu3.domain.factory.PaymentStrategyFactory

internal data class ConsoleDependencies(
    val getAllProducts: GetAllProductsUseCase,
    val getFilteredProducts: GetFilteredProductsUseCase,
    val addToCart: AddProductToCartUseCase,
    val removeFromCart: RemoveProductFromCartUseCase,
    val getCart: GetCartUseCase,
    val clearCart: ClearCartUseCase,
    val checkout: CheckoutUseCase,
    val getOrderHistory: GetOrderHistoryUseCase,
    val paymentStrategyFactory: PaymentStrategyFactory,
    val calculator: GodDiscountCalculator,
)