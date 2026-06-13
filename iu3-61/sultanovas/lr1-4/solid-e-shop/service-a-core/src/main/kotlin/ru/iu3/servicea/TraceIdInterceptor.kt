package ru.iu3.servicea

import io.grpc.*
import io.grpc.ForwardingServerCall.SimpleForwardingServerCall
import io.grpc.ForwardingServerCallListener.SimpleForwardingServerCallListener
import org.slf4j.MDC
import java.util.UUID

/**
 * Перехватчик для Service A:
 * 1. Извлекает Trace ID из метаданных запроса или генерирует новый
 * 2. Кладёт Trace ID в MDC на всё время обработки RPC (во всех коллбеках листенера)
 * 3. Возвращает Trace ID в ответных заголовках
 *
 * Проброс Trace ID в исходящие вызовы к Service B делается на стороне клиента
 * (ReferenceServiceClient) через TraceIdContext.createTraceIdMetadata().
 */
class TraceIdInterceptor : ServerInterceptor {

    companion object {
        const val TRACE_ID_KEY = "trace-id"
        const val MDC_KEY = "traceId"

        val TRACE_ID_METADATA_KEY: Metadata.Key<String> =
            Metadata.Key.of(TRACE_ID_KEY, Metadata.ASCII_STRING_MARSHALLER)
    }

    override fun <ReqT, RespT> interceptCall(
        call: ServerCall<ReqT, RespT>,
        headers: Metadata,
        next: ServerCallHandler<ReqT, RespT>
    ): ServerCall.Listener<ReqT> {

        val traceId = headers.get(TRACE_ID_METADATA_KEY)
            ?.takeIf { it.isNotBlank() }
            ?: UUID.randomUUID().toString()

        // Возвращаем trace-id клиенту в ответных заголовках
        val wrappedCall = object : SimpleForwardingServerCall<ReqT, RespT>(call) {
            override fun sendHeaders(responseHeaders: Metadata) {
                responseHeaders.put(TRACE_ID_METADATA_KEY, traceId)
                super.sendHeaders(responseHeaders)
            }
        }

        val listener = next.startCall(wrappedCall, headers)

        // Оборачиваем листенер так, чтобы MDC был выставлен во всех коллбеках
        return object : SimpleForwardingServerCallListener<ReqT>(listener) {
            override fun onMessage(message: ReqT) = withMdc { super.onMessage(message) }
            override fun onHalfClose() = withMdc { super.onHalfClose() }
            override fun onCancel() = withMdc { super.onCancel() }
            override fun onComplete() = withMdc { super.onComplete() }
            override fun onReady() = withMdc { super.onReady() }

            private inline fun withMdc(block: () -> Unit) {
                val previous = MDC.get(MDC_KEY)
                MDC.put(MDC_KEY, traceId)
                try {
                    block()
                } finally {
                    if (previous != null) MDC.put(MDC_KEY, previous) else MDC.remove(MDC_KEY)
                }
            }
        }
    }
}

/**
 * Утилита для получения текущего Trace ID из MDC и подкладывания его
 * в метаданные исходящих вызовов (например, к Reference Service).
 */
object TraceIdContext {
    const val MDC_KEY = "traceId"
    const val TRACE_ID_KEY = "trace-id"

    fun getCurrentTraceId(): String {
        return MDC.get(MDC_KEY) ?: "no-trace-id"
    }

    fun createTraceIdMetadata(): Metadata {
        val metadata = Metadata()
        val key = Metadata.Key.of(TRACE_ID_KEY, Metadata.ASCII_STRING_MARSHALLER)
        metadata.put(key, getCurrentTraceId())
        return metadata
    }
}