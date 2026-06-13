package ru.iu3.domain.model

internal sealed interface ProductFilter {

    data class CategoryFilter(val category: Category) : ProductFilter

    data class PriceFilter(val min: Double, val max: Double) : ProductFilter
}