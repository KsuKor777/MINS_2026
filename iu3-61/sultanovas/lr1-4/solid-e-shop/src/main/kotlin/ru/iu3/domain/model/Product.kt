package ru.iu3.domain.model

internal data class Product(
    val id: String,
    val title: String,
    val description: String,
    val price: Double,
    val category: Category,
)