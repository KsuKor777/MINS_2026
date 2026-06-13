package ru.iu3.domain.model

internal data class CartItem(
    val product: Product,
    val amount: Int,
) {

    fun getTotalPrice(): Double = product.price * amount
}