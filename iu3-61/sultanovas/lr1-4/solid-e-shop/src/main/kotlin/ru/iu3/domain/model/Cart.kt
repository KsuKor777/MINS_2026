package ru.iu3.domain.model

import ru.iu3.domain.exception.InvalidAmountException
import ru.iu3.domain.exception.ProductNotFoundException

internal class Cart(
    items: List<CartItem> = emptyList(),
) {
    private val itemsStorage: MutableList<CartItem> = items.toMutableList()

    fun getItems(): List<CartItem> = itemsStorage.toList()

    fun getTotalPrice(): Double = itemsStorage.sumOf { it.getTotalPrice() }

    fun add(product: Product, amount: Int = 1) {
        val index = itemsStorage.indexOfFirst { it.product.id == product.id }

        if (index == -1) {
            itemsStorage.add(CartItem(product, amount))
            return
        }

        val currentItem = itemsStorage[index]
        itemsStorage[index] = currentItem.copy(amount = currentItem.amount + amount)
    }

    fun remove(product: Product, amount: Int = 1) {
        val index = itemsStorage.indexOfFirst { it.product.id == product.id }
        if (index == -1) throw ProductNotFoundException(product.id)

        val currentItem = itemsStorage[index]
        val newAmount = currentItem.amount - amount

        when {
            newAmount > 0 -> itemsStorage[index] = currentItem.copy(amount = newAmount)
            newAmount == 0 -> itemsStorage.removeAt(index)
            else -> throw InvalidAmountException()
        }
    }

    fun isEmpty(): Boolean = itemsStorage.isEmpty()

    fun clear() {
        itemsStorage.clear()
    }
}