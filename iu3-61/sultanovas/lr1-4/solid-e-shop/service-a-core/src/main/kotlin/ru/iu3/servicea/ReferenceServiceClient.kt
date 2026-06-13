package ru.iu3.servicea

import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import io.grpc.StatusRuntimeException
import io.grpc.stub.MetadataUtils
import org.slf4j.LoggerFactory
import ru.iu3.grpc.*
import java.util.concurrent.TimeUnit

/**
 * Клиент для вызова Reference Service (Service B)
 * 
 * Реализует:
 * - Таймауты на вызовы
 * - Обработку ошибок соединения
 * - Retry-логику с экспоненциальной задержкой
 * - Передачу Trace ID в метаданных
 */
class ReferenceServiceClient(
    host: String = "localhost",
    port: Int = 50052,
    private val timeoutMs: Long = 5000,
    private val maxRetries: Int = 3,
    private val initialRetryDelayMs: Long = 100
) {
    private val logger = LoggerFactory.getLogger(ReferenceServiceClient::class.java)
    
    private val channel: ManagedChannel = ManagedChannelBuilder
        .forAddress(host, port)
        .usePlaintext()
        .keepAliveTime(30, TimeUnit.SECONDS)
        .keepAliveTimeout(10, TimeUnit.SECONDS)
        .build()

    private val blockingStub: ReferenceServiceGrpc.ReferenceServiceBlockingStub = 
        ReferenceServiceGrpc.newBlockingStub(channel)

    /**
     * Получить все товары с retry-логикой
     */
    fun getAllProducts(): List<Product> {
        return executeWithRetry("getAllProducts") {
            val metadata = TraceIdContext.createTraceIdMetadata()
            val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                .withDeadlineAfter(timeoutMs, TimeUnit.MILLISECONDS)
            
            val response = stub.getAllProducts(GetAllProductsRequest.newBuilder().build())
            logger.debug("getAllProducts: Получено {} товаров от Reference Service", response.productsCount)
            response.productsList
        }
    }

    /**
     * Получить товар по ID с retry-логикой
     */
    fun getProductById(productId: String): Product? {
        return executeWithRetry("getProductById") {
            val metadata = TraceIdContext.createTraceIdMetadata()
            val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                .withDeadlineAfter(timeoutMs, TimeUnit.MILLISECONDS)
            
            val request = GetProductByIdRequest.newBuilder().setProductId(productId).build()
            val response = stub.getProductById(request)
            
            if (response.found) {
                logger.debug("getProductById: Товар {} найден", productId)
                response.product
            } else {
                logger.warn("getProductById: Товар {} не найден", productId)
                null
            }
        }
    }

    /**
     * Валидировать существование товара
     */
    fun validateProductExists(productId: String): Boolean {
        return executeWithRetry("validateProductExists") {
            val metadata = TraceIdContext.createTraceIdMetadata()
            val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                .withDeadlineAfter(timeoutMs, TimeUnit.MILLISECONDS)
            
            val request = ValidateProductExistsRequest.newBuilder().setProductId(productId).build()
            val response = stub.validateProductExists(request)
            
            logger.debug("validateProductExists: Товар {} существует={}", productId, response.exists)
            response.exists
        }
    }

    /**
     * Валидировать цену товара
     */
    fun validateProductPrice(productId: String, expectedPrice: Double): PriceValidationResult {
        return executeWithRetry("validateProductPrice") {
            val metadata = TraceIdContext.createTraceIdMetadata()
            val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                .withDeadlineAfter(timeoutMs, TimeUnit.MILLISECONDS)
            
            val request = ValidateProductPriceRequest.newBuilder()
                .setProductId(productId)
                .setExpectedPrice(expectedPrice)
                .build()
            val response = stub.validateProductPrice(request)
            
            logger.debug("validateProductPrice: Товар {} цена валидна={}", productId, response.valid)
            PriceValidationResult(
                isValid = response.valid,
                actualPrice = response.actualPrice
            )
        }
    }

    /**
     * Получить товары по категории
     */
    fun getProductsByCategory(category: String): List<Product> {
        return executeWithRetry("getProductsByCategory") {
            val metadata = TraceIdContext.createTraceIdMetadata()
            val stub = blockingStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                .withDeadlineAfter(timeoutMs, TimeUnit.MILLISECONDS)
            
            val request = GetProductsByCategoryRequest.newBuilder().setCategory(category).build()
            val response = stub.getProductsByCategory(request)
            
            logger.debug("getProductsByCategory: Найдено {} товаров в категории {}", 
                response.productsCount, category)
            response.productsList
        }
    }

    /**
     * Выполнить вызов с retry-логикой и экспоненциальной задержкой
     */
    private fun <T> executeWithRetry(operation: String, block: () -> T): T {
        var lastException: Exception? = null
        var delayMs = initialRetryDelayMs

        for (attempt in 1..maxRetries) {
            try {
                return block()
            } catch (e: StatusRuntimeException) {
                lastException = e
                logger.warn("{}: Попытка {}/{} не удалась: {} (status={})", 
                    operation, attempt, maxRetries, e.message, e.status.code)
                
                if (attempt < maxRetries && isRetryable(e)) {
                    logger.info("{}: Retry через {} мс...", operation, delayMs)
                    Thread.sleep(delayMs)
                    delayMs *= 2 // Экспоненциальная задержка
                } else {
                    break
                }
            } catch (e: Exception) {
                lastException = e
                logger.error("{}: Неожиданная ошибка на попытке {}/{}: {}", 
                    operation, attempt, maxRetries, e.message, e)
                
                if (attempt < maxRetries) {
                    logger.info("{}: Retry через {} мс...", operation, delayMs)
                    Thread.sleep(delayMs)
                    delayMs *= 2
                } else {
                    break
                }
            }
        }

        throw ReferenceServiceUnavailableException(
            message = "Reference Service недоступен после $maxRetries попыток. Операция: $operation",
            cause = lastException
        )
    }

    /**
     * Проверить, является ли ошибка retryable
     */
    private fun isRetryable(e: StatusRuntimeException): Boolean {
        return when (e.status.code) {
            io.grpc.Status.Code.UNAVAILABLE -> true
            io.grpc.Status.Code.DEADLINE_EXCEEDED -> true
            io.grpc.Status.Code.RESOURCE_EXHAUSTED -> true
            else -> false
        }
    }

    /**
     * Закрыть соединение
     */
    fun close() {
        try {
            channel.shutdown().awaitTermination(5, TimeUnit.SECONDS)
            logger.info("Соединение с Reference Service закрыто")
        } catch (e: InterruptedException) {
            logger.error("Прерывание при закрытии соединения", e)
            Thread.currentThread().interrupt()
            channel.shutdownNow()
        }
    }
}

/**
 * Результат валидации цены
 */
data class PriceValidationResult(
    val isValid: Boolean,
    val actualPrice: Double
)

/**
 * Исключение недоступности Reference Service
 */
class ReferenceServiceUnavailableException(
    message: String,
    cause: Throwable? = null
) : RuntimeException(message, cause)
