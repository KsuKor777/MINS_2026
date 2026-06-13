package ru.iu3.di

import ru.iu3.application.generator.IdGenerator
import ru.iu3.application.usecase.impl.*
import ru.iu3.domain.observer.OrderEventPublisher
import ru.iu3.domain.repository.CartRepository
import ru.iu3.domain.repository.OrderRepository
import ru.iu3.domain.repository.ProductRepository
import ru.iu3.infrastructure.factory.PaymentStrategyFactoryImpl
import ru.iu3.infrastructure.generator.UuidGenerator
import ru.iu3.infrastructure.observer.EmailOrderObserver
import ru.iu3.infrastructure.observer.SmsOrderObserver
import ru.iu3.infrastructure.strategy.BonusPaymentStrategy
import ru.iu3.infrastructure.strategy.CardPaymentStrategy
import ru.iu3.infrastructure.strategy.CashPaymentStrategy
import ru.iu3.infrastructure.repository.CartRepositoryImpl
import ru.iu3.infrastructure.repository.OrderRepositoryImpl
import ru.iu3.infrastructure.repository.ProductRepositoryImpl
import ru.iu3.infrastructure.seed.StaticProducts
import ru.iu3.presentation.console.ConsoleDependencies
import ru.iu3.presentation.console.GodDiscountCalculator

internal object AppFactory {

    fun createConsoleDeps(): ConsoleDependencies {
        val products = StaticProducts.load()

        val productRepository: ProductRepository = ProductRepositoryImpl(products)
        val cartRepository: CartRepository = CartRepositoryImpl()
        val orderRepository: OrderRepository = OrderRepositoryImpl()

        val idGenerator: IdGenerator = UuidGenerator()
        val paymentStrategies = listOf(CardPaymentStrategy(), CashPaymentStrategy(), BonusPaymentStrategy())
        val paymentStrategyFactory = PaymentStrategyFactoryImpl(paymentStrategies)
        val orderEventPublisher = OrderEventPublisher()

        orderEventPublisher.subscribe(EmailOrderObserver())
        orderEventPublisher.subscribe(SmsOrderObserver())

        val calculator = GodDiscountCalculator(productRepository, cartRepository)

        return ConsoleDependencies(
            getAllProducts = GetAllProductsUseCaseImpl(productRepository),
            getFilteredProducts = GetFilteredProductsUseCaseImpl(productRepository),
            addToCart = AddProductToCartUseCaseImpl(productRepository, cartRepository),
            removeFromCart = RemoveProductFromCartUseCaseImpl(productRepository, cartRepository),
            getCart = GetCartUseCaseImpl(cartRepository),
            clearCart = ClearCartUseCaseImpl(cartRepository),
            checkout = CheckoutUseCaseImpl(
                cartRepository = cartRepository,
                orderRepository = orderRepository,
                idGenerator = idGenerator,
                eventPublisher = orderEventPublisher,
                strategyFactory = paymentStrategyFactory
            ),
            getOrderHistory = GetOrderHistoryUseCaseImpl(orderRepository),
            paymentStrategyFactory = paymentStrategyFactory,
            calculator = calculator,
        )
    }
}