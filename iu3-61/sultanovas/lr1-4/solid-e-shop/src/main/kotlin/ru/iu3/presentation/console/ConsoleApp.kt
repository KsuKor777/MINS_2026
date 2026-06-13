package ru.iu3.presentation.console

import ru.iu3.domain.exception.PaymentMethodNotFoundException
import ru.iu3.domain.exception.ShopException
import ru.iu3.domain.model.Category
import ru.iu3.domain.model.Product
import ru.iu3.domain.model.ProductFilter

internal class ConsoleApp(
    private val deps: ConsoleDependencies,
    private val userId: String,
) {

    fun run() {
        while (true) {
            printMenu()

            when (readInt("Выберите пункт: ")) {
                1 -> showAllProducts()
                2 -> showFilteredProducts()
                3 -> addToCart()
                4 -> removeFromCart()
                5 -> showCart()
                6 -> clearCart()
                7 -> checkout()
                8 -> showOrderHistory()
                9 -> calculateEstimatedCost()
                0 -> return
                else -> println("Неизвестная команда")
            }

            println()
        }
    }

    private fun printMenu() {
        println("=== Интернет-магазин ===")
        println("1) Показать все товары")
        println("2) Фильтр товаров")
        println("3) Добавить товар в корзину")
        println("4) Удалить товар из корзины")
        println("5) Показать корзину")
        println("6) Очистить корзину")
        println("7) Оформить заказ")
        println("8) История заказов")
        println("9) Калькулятор стоимости")
        println("0) Выход")
    }

    private fun showAllProducts() = handle {
        val products = deps.getAllProducts()
        printProducts(products)
    }

    private fun showFilteredProducts() = handle {
        println("Фильтры:")
        println("1) По категории")
        println("2) По цене")
        when (readInt("Выберите фильтр: ")) {
            1 -> {
                val category = readCategory()
                val products = deps.getFilteredProducts(ProductFilter.CategoryFilter(category))
                printProducts(products)
            }
            2 -> {
                val min = readDouble("Мин. цена: ")
                val max = readDouble("Макс. цена: ")
                val products = deps.getFilteredProducts(ProductFilter.PriceFilter(min, max))
                printProducts(products)
            }
            else -> println("Неизвестный фильтр")
        }
    }

    private fun addToCart() = handle {
        val productId = readString("Введите id товара: ")
        val amount = readInt("Количество: ")
        deps.addToCart(productId, amount)
        println("Добавлено в корзину")
    }

    private fun removeFromCart() = handle {
        val productId = readString("Введите id товара: ")
        val amount = readInt("Количество: ")
        deps.removeFromCart(productId, amount)
        println("Удалено из корзины")
    }

    private fun showCart() = handle {
        val cart = deps.getCart()
        val items = cart.getItems()
        if (items.isEmpty()) {
            println("Корзина пуста")
            return@handle
        }

        println("Корзина:")
        items.forEachIndexed { i, item ->
            println("${i + 1}) ${item.product.title} (id=${item.product.id}) x${item.amount} = ${formatPrice(item.getTotalPrice())}")
        }
        println("Итого: ${formatPrice(cart.getTotalPrice())}")
    }

    private fun clearCart() = handle {
        deps.clearCart()
        println("Корзина очищена")
    }

    private fun checkout() = handle {
        val strategyName = readPaymentStrategyName()
        val order = deps.checkout(userId, strategyName)

        println("Заказ оформлен:")
        println("id=${order.id}")
        println("status=${order.status}")
        println("payment=${order.paymentMethod}")
        println("total=${formatPrice(order.totalPrice)}")
        println("items=${order.items.size}")
    }

    private fun readPaymentStrategyName(): String {
        val strategies = deps.paymentStrategyFactory.getAll()

        println("Способы оплаты:")
        strategies.forEachIndexed { i, strategy ->
            println("${i + 1}) ${strategy.name}")
        }

        val idx = readInt("Выберите способ оплаты: ") - 1
        return strategies.getOrNull(idx)?.name ?: throw PaymentMethodNotFoundException()
    }

    private fun showOrderHistory() = handle {
        val orders = deps.getOrderHistory(userId)
        if (orders.isEmpty()) {
            println("История пуста")
            return@handle
        }

        println("История заказов:")
        orders.forEachIndexed { i, o ->
            println("${i + 1}) id=${o.id} status=${o.status} payment=${o.paymentMethod} total=${formatPrice(o.totalPrice)} items=${o.items.size}")
        }
    }

    private fun calculateEstimatedCost() = handle {
        val paymentMethod = readPaymentStrategyName()
        deps.calculator.calculateAndPrint(paymentMethod = paymentMethod)
    }

    private inline fun handle(block: () -> Unit) {
        try {
            block()
        } catch (e: ShopException) {
            println("Ошибка: ${e.message}")
        } catch (e: Exception) {
            println("Непредвиденная ошибка: ${e::class.simpleName}: ${e.message}")
        }
    }

    private fun printProducts(products: List<Product>) {
        if (products.isEmpty()) {
            println("Ничего не найдено")
            return
        }
        products.forEach { p ->
            println("id=${p.id} | ${p.title} | ${p.category} | ${formatPrice(p.price)}")
        }
    }

    private fun readCategory(): Category {
        println("Категории:")
        Category.entries.forEachIndexed { i, c -> println("${i + 1}) $c") }
        val idx = readInt("Выберите категорию: ") - 1
        return Category.entries.getOrNull(idx) ?: Category.OTHER
    }

    private fun readString(prompt: String): String {
        print(prompt)
        return readln().trim()
    }

    private fun readInt(prompt: String): Int {
        while (true) {
            print(prompt)
            val s = readln().trim()
            val v = s.toIntOrNull()
            if (v != null) return v
            println("Введите целое число")
        }
    }

    private fun readDouble(prompt: String): Double {
        while (true) {
            print(prompt)
            val s = readln().trim().replace(',', '.')
            val v = s.toDoubleOrNull()
            if (v != null) return v
            println("Введите число")
        }
    }

    private fun formatPrice(v: Double): String = "%.2f".format(v)
}
