package ru.iu3.infrastructure.seed

import ru.iu3.domain.model.Category
import ru.iu3.domain.model.Product

internal object StaticProducts {

    fun load(): List<Product> = listOf(
        Product("p1","Snowboard Nitro Prime","Универсальная доска для начинающих",29990.0, Category.SNOWBOARDS),
        Product("p2","Bindings Burton Freestyle","Крепления для парка и склона",15990.0, Category.BINDINGS),
        Product("p3","Boots DC Control","Ботинки средней жёсткости",18990.0, Category.BOOTS),
        Product("p4","Helmet Smith Mission","Лёгкий защитный шлем",9990.0, Category.PROTECTION),
        Product("p5","Goggles Oakley Line Miner","Маска с широким обзором",12990.0, Category.ACCESSORIES),
    )
}