package ru.iu3.servicea

import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import io.grpc.Metadata
import io.grpc.stub.MetadataUtils
import org.slf4j.LoggerFactory
import ru.iu3.grpc.*
import java.util.UUID
import java.util.concurrent.TimeUnit

/**
 * Тестовый клиент для демонстрации работы микросервисов
 * 
 * Используется для:
 * 1. Тестирования нормальной работы
 * 2. Тестирования сценария недоступности Service B
 */
class TestClient(
    host: String = "localhost",
    port: Int = 50051,
) {
    private val logger = LoggerFactory.getLogger(TestClient::class.java)
    
    private val channel: ManagedChannel = ManagedChannelBuilder
        .forAddress(host, port)
        .usePlaintext()
        .build()

    private val blockingStub: CoreServiceGrpc.CoreServiceBlockingStub = 
        CoreServiceGrpc.newBlockingStub(channel)

    private val traceId = UUID.randomUUID().toString()

    /**
     * Создать метаданные с Trace ID
     */
    private fun createHeaders(): Metadata {
        val metadata = Metadata()
        val key = Metadata.Key.of("trace-id", Metadata.ASCII_STRING_MARSHALLER)
        metadata.put(key, traceId)
        return metadata
    }

    /**
     * Добавить товар в корзину
     */
    fun addToCart(userId: String, productId: String, quantity: Int): AddToCartResponse {
        logger.info("=== ТЕСТ: Добавление товара в корзину ===")
        logger.info("UserID: {}, ProductID: {}, Quantity: {}", userId, productId, quantity)

        val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(createHeaders()))
        
        val request = AddToCartRequest.newBuilder()
            .setUserId(userId)
            .setProductId(productId)
            .setQuantity(quantity)
            .build()

        return try {
            val response = stub.addToCart(request)
            logger.info("Результат: success={}, message={}", response.success, response.message)
            if (response.hasCart()) {
                logger.info("Корзина: {} товаров, общая сумма: {}", response.cart.itemsCount, response.cart.totalPrice)
            }
            response
        } catch (e: Exception) {
            logger.error("Ошибка: {}", e.message)
            throw e
        }
    }

    /**
     * Получить корзину
     */
    fun getCart(userId: String): GetCartResponse {
        logger.info("=== ТЕСТ: Получение корзины ===")
        logger.info("UserID: {}", userId)

        val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(createHeaders()))
        
        val request = GetCartRequest.newBuilder().setUserId(userId).build()

        return try {
            val response = stub.getCart(request)
            logger.info("Корзина: {} товаров, общая сумма: {}", response.cart.itemsCount, response.cart.totalPrice)
            response.cart.itemsList.forEach { item ->
                logger.info("  - {} (x{}) = {}", item.productTitle, item.quantity, item.subtotal)
            }
            response
        } catch (e: Exception) {
            logger.error("Ошибка: {}", e.message)
            throw e
        }
    }

    /**
     * Оформить заказ
     */
    fun checkout(userId: String, paymentMethod: String): CheckoutResponse {
        logger.info("=== ТЕСТ: Оформление заказа ===")
        logger.info("UserID: {}, PaymentMethod: {}", userId, paymentMethod)

        val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(createHeaders()))
        
        val request = CheckoutRequest.newBuilder()
            .setUserId(userId)
            .setPaymentMethod(paymentMethod)
            .build()

        return try {
            val response = stub.checkout(request)
            logger.info("Результат: success={}, message={}", response.success, response.message)
            if (response.hasOrder()) {
                logger.info("Заказ: ID={}, сумма={}, статус={}", 
                    response.order.id, response.order.totalAmount, response.order.status)
            }
            response
        } catch (e: Exception) {
            logger.error("Ошибка: {}", e.message)
            throw e
        }
    }

    /**
     * Получить историю заказов
     */
    fun getOrderHistory(userId: String): GetOrderHistoryResponse {
        logger.info("=== ТЕСТ: История заказов ===")
        logger.info("UserID: {}", userId)

        val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(createHeaders()))
        
        val request = GetOrderHistoryRequest.newBuilder().setUserId(userId).build()

        return try {
            val response = stub.getOrderHistory(request)
            logger.info("Найдено заказов: {}", response.ordersCount)
            response.ordersList.forEach { order ->
                logger.info("  - Заказ {}: сумма={}, статус={}", order.id, order.totalAmount, order.status)
            }
            response
        } catch (e: Exception) {
            logger.error("Ошибка: {}", e.message)
            throw e
        }
    }

    /**
     * Запустить демонстрационный сценарий
     */
    fun runDemo() {
        val userId = "user-" + UUID.randomUUID().toString().take(8)
        
        logger.info("========================================")
        logger.info("ДЕМОНСТРАЦИЯ РАБОТЫ МИКРОСЕРВИСОВ")
        logger.info("Trace ID: {}", traceId)
        logger.info("User ID: {}", userId)
        logger.info("========================================")

        try {
            // Добавляем товары в корзину
            addToCart(userId, "p1", 1)  // Snowboard
            addToCart(userId, "p2", 2)  // Bindings
            addToCart(userId, "p4", 1)  // Helmet

            // Получаем корзину
            getCart(userId)

            // Оформляем заказ
            checkout(userId, "CARD")

            // Получаем историю заказов
            getOrderHistory(userId)

            logger.info("========================================")
            logger.info("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
            logger.info("========================================")

        } catch (e: Exception) {
            logger.error("ДЕМОНСТРАЦИЯ ПРЕРВАНА: {}", e.message)
        }
    }

    /**
     * Закрыть соединение
     */
    fun close() {
        try {
            channel.shutdown().awaitTermination(5, TimeUnit.SECONDS)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
            channel.shutdownNow()
        }
    }
}

fun main() {
    val host = System.getenv("CORE_SERVICE_HOST") ?: "localhost"
    val port = System.getenv("CORE_SERVICE_PORT")?.toIntOrNull() ?: 50051

    val client = TestClient(host = host, port = port)
    
    try {
        client.runDemo()
    } finally {
        client.close()
    }
}
