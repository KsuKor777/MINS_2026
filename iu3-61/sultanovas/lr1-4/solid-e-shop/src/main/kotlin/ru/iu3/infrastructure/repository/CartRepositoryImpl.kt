package ru.iu3.infrastructure.repository

import ru.iu3.domain.model.Cart
import ru.iu3.domain.repository.CartRepository

internal class CartRepositoryImpl(
    private val cart: Cart = Cart(),
) : CartRepository {

    override fun get(): Cart = cart

    override fun clear() {
        cart.clear()
    }
}