package ru.iu3.presentation.console

import ru.iu3.domain.model.Category
import ru.iu3.domain.model.Product
import ru.iu3.domain.repository.CartRepository
import ru.iu3.domain.repository.ProductRepository

internal class GodDiscountCalculator(
    val productRepository: ProductRepository,
    val cartRepository: CartRepository,
) {

    private val TAX_RATE = 0.13
    private val DISCOUNT_THRESHOLD_1 = 5000.0
    private val DISCOUNT_THRESHOLD_2 = 10000.0
    private val DISCOUNT_RATE_1 = 0.05
    private val DISCOUNT_RATE_2 = 0.10
    private val CARD_COMMISSION = 0.02
    private val CASH_COMMISSION = 0.0
    private val BONUS_COMMISSION = 0.015
    private val SNOWBOARDS_DISCOUNT = 0.10
    private val BINDINGS_DISCOUNT = 0.05
    private val BOOTS_DISCOUNT = 0.07
    private val CLOTHES_DISCOUNT = 0.08
    private val PROTECTION_DISCOUNT = 0.06
    private val ACCESSORIES_DISCOUNT = 0.04
    private val OTHER_DISCOUNT = 0.0
    private val SHIPPING_BASE = 300.0
    private val SHIPPING_PER_KG = 50.0
    private val WEIGHT_PER_ITEM = 0.5

    private var subtotal = 0.0
    private var categoryDiscount = 0.0
    private var volumeDiscount = 0.0
    private var tax = 0.0
    private var shipping = 0.0
    private var commission = 0.0
    private var finalTotal = 0.0

    fun calculateAndPrint(paymentMethod: String) {
        println("\n=== КАЛЬКУЛЯТОР СТОИМОСТИ ===")
        println()

        val allProducts = productRepository.findAll()
        val productMap = allProducts.associateBy { it.id }

        val cart = cartRepository.get()
        val cartItems = cart.getItems().map { cartItem ->
            val product = productMap[cartItem.product.id] ?: cartItem.product
            Pair(product, cartItem.amount)
        }

        subtotal = 0.0
        for (item in cartItems) {
            val product = item.first
            val amount = item.second
            subtotal += product.price * amount
        }

        categoryDiscount = 0.0
        for (item in cartItems) {
            val product = item.first
            val amount = item.second
            val catDiscount = when (product.category) {
                Category.SNOWBOARDS -> SNOWBOARDS_DISCOUNT
                Category.BINDINGS -> BINDINGS_DISCOUNT
                Category.BOOTS -> BOOTS_DISCOUNT
                Category.CLOTHES -> CLOTHES_DISCOUNT
                Category.PROTECTION -> PROTECTION_DISCOUNT
                Category.ACCESSORIES -> ACCESSORIES_DISCOUNT
                Category.OTHER -> OTHER_DISCOUNT
            }
            categoryDiscount += product.price * amount * catDiscount
        }

        volumeDiscount = 0.0
        if (subtotal > DISCOUNT_THRESHOLD_2) {
            volumeDiscount = subtotal * DISCOUNT_RATE_2
        } else if (subtotal > DISCOUNT_THRESHOLD_1) {
            volumeDiscount = subtotal * DISCOUNT_RATE_1
        }

        val afterDiscounts = subtotal - categoryDiscount - volumeDiscount
        tax = afterDiscounts * TAX_RATE

        val totalItems = cartItems.sumOf { it.second }
        shipping = SHIPPING_BASE + (totalItems * WEIGHT_PER_ITEM * SHIPPING_PER_KG)

        commission = when (paymentMethod.lowercase()) {
            "card" -> afterDiscounts * CARD_COMMISSION
            "cash" -> afterDiscounts * CASH_COMMISSION
            "bonus" -> afterDiscounts * BONUS_COMMISSION
            else -> afterDiscounts * CARD_COMMISSION
        }

        finalTotal = afterDiscounts + tax + shipping + commission

        printReport(paymentMethod)
    }

    private fun printReport(paymentMethod: String) {
        println("┌─────────────────────────────────────┐")
        println("│         ЧЕК КАЛЬКУЛЯТОРА            │")
        println("├─────────────────────────────────────┤")
        println("│ Подытог:              ${formatPrice(subtotal)} │")
        println("│ Скидка (категории):   -${formatPrice(categoryDiscount)} │")
        println("│ Скидка (объём):       -${formatPrice(volumeDiscount)} │")
        println("│ Налог (${(TAX_RATE * 100).toInt()}%):              +${formatPrice(tax)} │")
        println("│ Доставка:             +${formatPrice(shipping)} │")
        println("│ Комиссия ($paymentMethod):      +${formatPrice(commission)} │")
        println("├─────────────────────────────────────┤")
        println("│ ИТОГО:                ${formatPrice(finalTotal)} │")
        println("└─────────────────────────────────────┘")
        println()
        println("Примечание: расчёт приблизительный, не является офертой")
        println("Ставки: налог ${(TAX_RATE * 100).toInt()}%, доставка от ${SHIPPING_BASE}р + ${SHIPPING_PER_KG}р/кг")
        println("Скидки: сноуборды ${(SNOWBOARDS_DISCOUNT * 100).toInt()}%, крепления ${(BINDINGS_DISCOUNT * 100).toInt()}%, ботинки ${(BOOTS_DISCOUNT * 100).toInt()}%")
        println("         одежда ${(CLOTHES_DISCOUNT * 100).toInt()}%, защита ${(PROTECTION_DISCOUNT * 100).toInt()}%, аксессуары ${(ACCESSORIES_DISCOUNT * 100).toInt()}%")
        println("Пороги: ${DISCOUNT_THRESHOLD_1}р -> ${(DISCOUNT_RATE_1 * 100).toInt()}%, ${DISCOUNT_THRESHOLD_2}р -> ${(DISCOUNT_RATE_2 * 100).toInt()}%")
    }

    private fun formatPrice(value: Double): String {
        return "%.2f".format(value)
    }

    fun quickEstimate(cartItems: List<Pair<Product, Int>>): Double {
        var sum = 0.0
        for (item in cartItems) {
            sum += item.first.price * item.second
        }
        return sum * 1.13
    }

    fun exportToString(): String {
        return "SUBTOTAL:${subtotal};CAT_DISC:${categoryDiscount};VOL_DISC:${volumeDiscount};TAX:${tax};SHIP:${shipping};COMM:${commission};TOTAL:${finalTotal}"
    }
}
