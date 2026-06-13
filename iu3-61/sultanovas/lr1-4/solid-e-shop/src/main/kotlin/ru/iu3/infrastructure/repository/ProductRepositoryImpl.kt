package ru.iu3.infrastructure.repository

import ru.iu3.domain.exception.InvalidAmountException
import ru.iu3.domain.exception.InvalidFilterException
import ru.iu3.domain.model.Product
import ru.iu3.domain.model.ProductFilter
import ru.iu3.domain.repository.ProductRepository

internal class ProductRepositoryImpl(
    initialProducts: List<Product>,
    initialStock: Map<String, Int> = initialProducts.associate { it.id to Int.MAX_VALUE },
) : ProductRepository {

    private val productsById: MutableMap<String, Product> = initialProducts.associateBy { it.id }.toMutableMap()
    private val stockByProductId: MutableMap<String, Int> = initialStock.toMutableMap()

    override fun findAll(): List<Product> = productsById.values.toList()

    override fun findById(productId: String): Product? = productsById[productId]

    override fun findByFilter(filter: ProductFilter): List<Product> {
        val all = findAll()

        return when (filter) {
            is ProductFilter.CategoryFilter ->
                all.filter { it.category == filter.category }

            is ProductFilter.PriceFilter -> {
                if (filter.min < 0 || filter.max < 0 || filter.min > filter.max) throw InvalidFilterException()
                all.filter { it.price in filter.min..filter.max }
            }
        }
    }

    override fun removeProduct(productId: String, amount: Int) {
        if (amount <= 0) throw InvalidAmountException()
        val current = stockByProductId[productId] ?: return
        val newValue = current - amount
        if (newValue < 0) throw InvalidAmountException()
        stockByProductId[productId] = newValue
    }

    fun getStock(productId: String): Int? = stockByProductId[productId]
}