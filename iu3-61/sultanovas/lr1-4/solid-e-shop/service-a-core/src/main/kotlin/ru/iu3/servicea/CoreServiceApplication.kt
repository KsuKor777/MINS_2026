package ru.iu3.servicea

import io.grpc.Server
import io.grpc.ServerBuilder
import org.slf4j.LoggerFactory
import java.util.concurrent.TimeUnit

/**
 * Service A - Core Service (Основной сервис)
 * 
 * Содержит основную бизнес-логику:
 * - Управление корзиной
 * - Оформление заказов
 * - Транзакции
 * 
 * Вызывает Service B для получения справочных данных и валидации
 */
class CoreServiceApplication(
    private val port: Int = 50051,
    private val referenceServiceHost: String = "localhost",
    private val referenceServicePort: Int = 50052
) {
    private val logger = LoggerFactory.getLogger(CoreServiceApplication::class.java)
    private var server: Server? = null
    private var referenceServiceClient: ReferenceServiceClient? = null

    fun start() {
        // Создаём клиент для вызова Service B
        referenceServiceClient = ReferenceServiceClient(
            host = referenceServiceHost,
            port = referenceServicePort
        )

        // Создаём основной сервис с зависимостями
        val coreServiceImpl = CoreServiceImpl(referenceServiceClient!!)

        server = ServerBuilder
            .forPort(port)
            .addService(coreServiceImpl)
            .intercept(TraceIdInterceptor())
            .build()
            .start()

        logger.info("Service A (Core Service) started on port {}", port)
        logger.info("Connected to Reference Service at {}:{}", referenceServiceHost, referenceServicePort)
        logger.info("Press Ctrl+C to stop")

        Runtime.getRuntime().addShutdownHook(Thread {
            logger.info("Shutting down Service A...")
            this@CoreServiceApplication.stop()
            logger.info("Service A stopped")
        })
    }

    fun stop() {
        server?.apply {
            shutdown()
            try {
                awaitTermination(30, TimeUnit.SECONDS)
            } catch (e: InterruptedException) {
                logger.error("Interrupted during shutdown", e)
                Thread.currentThread().interrupt()
            }
        }
        referenceServiceClient?.close()
    }

    fun blockUntilShutdown() {
        server?.awaitTermination()
    }
}

fun main() {
    val port = System.getenv("CORE_SERVICE_PORT")?.toIntOrNull() ?: 50051
    val refHost = System.getenv("REFERENCE_SERVICE_HOST") ?: "localhost"
    val refPort = System.getenv("REFERENCE_SERVICE_PORT")?.toIntOrNull() ?: 50052

    val app = CoreServiceApplication(
        port = port,
        referenceServiceHost = refHost,
        referenceServicePort = refPort
    )
    app.start()
    app.blockUntilShutdown()
}
