package ru.iu3.serviceb

import io.grpc.Server
import io.grpc.ServerBuilder
import org.slf4j.LoggerFactory
import java.util.concurrent.TimeUnit

/**
 * Service B - Reference Service (Справочный сервис)
 * 
 * Предоставляет справочные данные:
 * - Каталог товаров
 * - Категории
 * - Валидация товаров и цен
 * 
 * Логирует все входящие запросы с Trace ID
 */
class ReferenceServiceApplication(
    private val port: Int = 50052,
) {
    private val logger = LoggerFactory.getLogger(ReferenceServiceApplication::class.java)
    private var server: Server? = null

    fun start() {
        val referenceServiceImpl = ReferenceServiceImpl()
        
        server = ServerBuilder
            .forPort(port)
            .addService(referenceServiceImpl)
            .intercept(TraceIdInterceptor())
            .build()
            .start()

        logger.info("Service B (Reference Service) started on port {}", port)
        logger.info("Press Ctrl+C to stop")

        Runtime.getRuntime().addShutdownHook(Thread {
            logger.info("Shutting down Service B...")
            this@ReferenceServiceApplication.stop()
            logger.info("Service B stopped")
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
    }

    fun blockUntilShutdown() {
        server?.awaitTermination()
    }
}

fun main() {
    val app = ReferenceServiceApplication(port = 50052)
    app.start()
    app.blockUntilShutdown()
}
