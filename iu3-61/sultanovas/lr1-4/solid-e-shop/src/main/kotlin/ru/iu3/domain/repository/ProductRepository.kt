package ru.iu3.domain.repository

import ru.iu3.domain.model.ProductFilter
import ru.iu3.domain.model.Product

internal interface ProductRepository {

    fun findAll(): List<Product>

    fun findById(productId: String): Product?

    fun findByFilter(filter: ProductFilter): List<Product>

    fun removeProduct(productId: String, amount: Int)
}