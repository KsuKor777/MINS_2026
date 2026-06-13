package ru.iu3.servicea

import io.grpc.Status
import io.grpc.stub.StreamObserver
import org.slf4j.LoggerFactory
import ru.iu3.grpc.*
import java.time.Instant
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

/**
 * Реализация Core Service (Service A)
 * 
 * Содержит основную бизнес-логику:
 * - Управление корзиной покупок
 * - Оформление заказов
 * - Валидация через Reference Service
 * 
 * Graceful обработка недоступности Service B
 */
class CoreServiceImpl(
    private val referenceServiceClient: ReferenceServiceClient
) : CoreServiceGrpc.CoreServiceImplBase() {

    private val logger = LoggerFactory.getLogger(CoreServiceImpl::class.java)

    // In-memory хранилище корзин (для демонстрации)
    private val carts = ConcurrentHashMap<String, MutableMap<String, CartItemData>>()

    // In-memory хранилище заказов
    private val orders = ConcurrentHashMap<String, MutableList<OrderData>>()

    // Данные элемента корзины
    data class CartItemData(
        val productId: String,
        val productTitle: String,
        val quantity: Int,
        val price: Double,
        val subtotal: Double
    )

    // Данные заказа
    data class OrderData(
        val id: String,
        val userId: String,
        val items: List<CartItemData>,
        val totalAmount: Double,
        val status: String,
        val createdAt: String,
        val paymentMethod: String
    )

    override fun addToCart(
        request: AddToCartRequest,
        responseObserver: StreamObserver<AddToCartResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("addToCart: Запрос добавления товара в корзину. UserID={}, ProductID={}, Quantity={}", 
            request.userId, request.productId, request.quantity)

        try {
            // Валидация товара через Reference Service
            val product = referenceServiceClient.getProductById(request.productId)
            
            if (product == null) {
                logger.warn("addToCart: Товар {} не найден в Reference Service", request.productId)
                sendError(responseObserver, "Товар с ID ${request.productId} не найден")
                return
            }

            // Добавление в корзину
            val cart = carts.getOrPut(request.userId) { mutableMapOf() }
            
            val existingItem = cart[request.productId]
            val newQuantity = (existingItem?.quantity ?: 0) + request.quantity
            val subtotal = newQuantity * product.price

            cart[request.productId] = CartItemData(
                productId = product.id,
                productTitle = product.title,
                quantity = newQuantity,
                price = product.price,
                subtotal = subtotal
            )

            logger.info("addToCart [{}]: Товар {} добавлен в корзину пользователя {}", 
                traceId, request.productId, request.userId)

            val response = AddToCartResponse.newBuilder()
                .setSuccess(true)
                .setMessage("Товар '${product.title}' добавлен в корзину")
                .setCart(convertCart(request.userId, cart))
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (e: ReferenceServiceUnavailableException) {
            logger.error("addToCart [{}]: Reference Service недоступен. {}", traceId, e.message)
            // Graceful degradation: возвращаем понятное сообщение пользователю
            val response = AddToCartResponse.newBuilder()
                .setSuccess(false)
                .setMessage("Сервис каталога временно недоступен. Попробуйте позже.")
                .build()
            responseObserver.onNext(response)
            responseObserver.onCompleted()
        } catch (e: Exception) {
            logger.error("addToCart [{}]: Неожиданная ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при добавлении товара в корзину")
        }
    }

    override fun getCart(
        request: GetCartRequest,
        responseObserver: StreamObserver<GetCartResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("getCart: Запрос корзины пользователя {}", request.userId)

        try {
            val cartItems = carts[request.userId] ?: emptyMap()
            val cart = convertCart(request.userId, cartItems)

            logger.info("getCart [{}]: Корзина пользователя {} содержит {} товаров на сумму {}", 
                traceId, request.userId, cart.itemsCount, cart.totalPrice)

            val response = GetCartResponse.newBuilder()
                .setCart(cart)
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (e: Exception) {
            logger.error("getCart [{}]: Ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при получении корзины")
        }
    }

    override fun removeFromCart(
        request: RemoveFromCartRequest,
        responseObserver: StreamObserver<RemoveFromCartResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("removeFromCart: Запрос удаления товара из корзины. UserID={}, ProductID={}", 
            request.userId, request.productId)

        try {
            val cart = carts[request.userId]
            
            if (cart == null || !cart.containsKey(request.productId)) {
                logger.warn("removeFromCart [{}]: Товар {} не найден в корзине пользователя {}", 
                    traceId, request.productId, request.userId)
                val response = RemoveFromCartResponse.newBuilder()
                    .setSuccess(false)
                    .setMessage("Товар не найден в корзине")
                    .build()
                responseObserver.onNext(response)
                responseObserver.onCompleted()
                return
            }

            cart.remove(request.productId)
            logger.info("removeFromCart [{}]: Товар {} удалён из корзины", traceId, request.productId)

            val response = RemoveFromCartResponse.newBuilder()
                .setSuccess(true)
                .setMessage("Товар удалён из корзины")
                .setCart(convertCart(request.userId, cart))
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (e: Exception) {
            logger.error("removeFromCart [{}]: Ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при удалении товара из корзины")
        }
    }

    override fun clearCart(
        request: ClearCartRequest,
        responseObserver: StreamObserver<ClearCartResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("clearCart: Запрос очистки корзины пользователя {}", request.userId)

        try {
            carts.remove(request.userId)
            logger.info("clearCart [{}]: Корзина пользователя {} очищена", traceId, request.userId)

            val response = ClearCartResponse.newBuilder()
                .setSuccess(true)
                .setMessage("Корзина очищена")
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (e: Exception) {
            logger.error("clearCart [{}]: Ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при очистке корзины")
        }
    }

    override fun checkout(
        request: CheckoutRequest,
        responseObserver: StreamObserver<CheckoutResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("checkout: Запрос оформления заказа. UserID={}, PaymentMethod={}", 
            request.userId, request.paymentMethod)

        try {
            val cartItems = carts[request.userId]
            
            if (cartItems == null || cartItems.isEmpty()) {
                logger.warn("checkout [{}]: Корзина пользователя {} пуста", traceId, request.userId)
                val response = CheckoutResponse.newBuilder()
                    .setSuccess(false)
                    .setMessage("Корзина пуста")
                    .build()
                responseObserver.onNext(response)
                responseObserver.onCompleted()
                return
            }

            // Валидация всех товаров через Reference Service
            val validatedItems = mutableListOf<CartItemData>()
            for ((productId, item) in cartItems) {
                try {
                    val exists = referenceServiceClient.validateProductExists(productId)
                    if (!exists) {
                        logger.warn("checkout [{}]: Товар {} больше не существует", traceId, productId)
                        val response = CheckoutResponse.newBuilder()
                            .setSuccess(false)
                            .setMessage("Товар '$productId' больше недоступен")
                            .build()
                        responseObserver.onNext(response)
                        responseObserver.onCompleted()
                        return
                    }
                    validatedItems.add(item)
                } catch (_: ReferenceServiceUnavailableException) {
                    // Graceful degradation: продолжаем без валидации, но логируем
                    logger.warn("checkout [{}]: Не удалось валидировать товар {} (Reference Service недоступен)", 
                        traceId, productId)
                    validatedItems.add(item)
                }
            }

            // Расчёт общей суммы
            val totalAmount = validatedItems.sumOf { it.subtotal }

            // Создание заказа
            val order = OrderData(
                id = UUID.randomUUID().toString(),
                userId = request.userId,
                items = validatedItems.toList(),
                totalAmount = totalAmount,
                status = "CONFIRMED",
                createdAt = Instant.now().toString(),
                paymentMethod = request.paymentMethod
            )

            orders.getOrPut(request.userId) { mutableListOf() }.add(order)

            // Очистка корзины
            carts.remove(request.userId)

            logger.info("checkout [{}]: Заказ {} оформлен на сумму {}", 
                traceId, order.id, totalAmount)

            val response = CheckoutResponse.newBuilder()
                .setSuccess(true)
                .setMessage("Заказ ${order.id} успешно оформлен")
                .setOrder(convertOrder(order))
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (_: ReferenceServiceUnavailableException) {
            logger.error("checkout [{}]: Reference Service недоступен во время оформления заказа", traceId)
            // Graceful degradation: позволяем оформить заказ без валидации
            val response = CheckoutResponse.newBuilder()
                .setSuccess(false)
                .setMessage("Сервис каталога временно недоступен. Оформление заказа невозможно.")
                .build()
            responseObserver.onNext(response)
            responseObserver.onCompleted()
        } catch (e: Exception) {
            logger.error("checkout [{}]: Ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при оформлении заказа")
        }
    }

    override fun getOrderHistory(
        request: GetOrderHistoryRequest,
        responseObserver: StreamObserver<GetOrderHistoryResponse>
    ) {
        val traceId = TraceIdContext.getCurrentTraceId()
        logger.info("getOrderHistory: Запрос истории заказов пользователя {}", request.userId)

        try {
            val userOrders = orders[request.userId] ?: emptyList()
            
            logger.info("getOrderHistory [{}]: Найдено {} заказов у пользователя {}", 
                traceId, userOrders.size, request.userId)

            val response = GetOrderHistoryResponse.newBuilder()
                .addAllOrders(userOrders.map { convertOrder(it) })
                .build()

            responseObserver.onNext(response)
            responseObserver.onCompleted()

        } catch (e: Exception) {
            logger.error("getOrderHistory [{}]: Ошибка: {}", traceId, e.message, e)
            sendError(responseObserver, "Произошла ошибка при получении истории заказов")
        }
    }

    // Утилиты конвертации
    private fun convertCart(userId: String, items: Map<String, CartItemData>): Cart {
        val cartBuilder = Cart.newBuilder().setUserId(userId)
        val totalPrice = items.values.sumOf { it.subtotal }
        cartBuilder.addAllItems(items.values.map { convertCartItem(it) })
        cartBuilder.setTotalPrice(totalPrice)
        return cartBuilder.build()
    }

    private fun convertCartItem(item: CartItemData): CartItem {
        return CartItem.newBuilder()
            .setProductId(item.productId)
            .setProductTitle(item.productTitle)
            .setQuantity(item.quantity)
            .setPrice(item.price)
            .setSubtotal(item.subtotal)
            .build()
    }

    private fun convertOrder(order: OrderData): Order {
        return Order.newBuilder()
            .setId(order.id)
            .setUserId(order.userId)
            .addAllItems(order.items.map { convertOrderItem(it) })
            .setTotalAmount(order.totalAmount)
            .setStatus(order.status)
            .setCreatedAt(order.createdAt)
            .setPaymentMethod(order.paymentMethod)
            .build()
    }

    private fun convertOrderItem(item: CartItemData): OrderItem {
        return OrderItem.newBuilder()
            .setProductId(item.productId)
            .setProductTitle(item.productTitle)
            .setQuantity(item.quantity)
            .setPrice(item.price)
            .setSubtotal(item.subtotal)
            .build()
    }

    private fun sendError(responseObserver: StreamObserver<*>, message: String) {
        responseObserver.onError(Status.INTERNAL.withDescription(message).asRuntimeException())
    }
}
