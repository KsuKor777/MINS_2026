package ru.iu3.serviceb

import io.grpc.stub.StreamObserver
import org.slf4j.LoggerFactory
import ru.iu3.grpc.*

/**
 * Реализация Reference Service (Service B)
 * 
 * Предоставляет справочные данные и валидацию
 */
class ReferenceServiceImpl : ReferenceServiceGrpc.ReferenceServiceImplBase() {

    private val logger = LoggerFactory.getLogger(ReferenceServiceImpl::class.java)

    // Моковые данные каталога товаров (используем builder для proto-классов)
    private val products = mapOf(
        "p1" to Product.newBuilder()
            .setId("p1")
            .setTitle("Snowboard Nitro Prime")
            .setDescription("Универсальная доска для начинающих")
            .setPrice(29990.0)
            .setCategory("SNOWBOARDS")
            .build(),
        "p2" to Product.newBuilder()
            .setId("p2")
            .setTitle("Bindings Burton Freestyle")
            .setDescription("Крепления для парка и склона")
            .setPrice(15990.0)
            .setCategory("BINDINGS")
            .build(),
        "p3" to Product.newBuilder()
            .setId("p3")
            .setTitle("Boots DC Control")
            .setDescription("Ботинки средней жёсткости")
            .setPrice(18990.0)
            .setCategory("BOOTS")
            .build(),
        "p4" to Product.newBuilder()
            .setId("p4")
            .setTitle("Helmet Smith Mission")
            .setDescription("Лёгкий защитный шлем")
            .setPrice(9990.0)
            .setCategory("PROTECTION")
            .build(),
        "p5" to Product.newBuilder()
            .setId("p5")
            .setTitle("Goggles Oakley Line Miner")
            .setDescription("Маска с широким обзором")
            .setPrice(12990.0)
            .setCategory("ACCESSORIES")
            .build()
    )

    private val categories = listOf(
        "SNOWBOARDS",
        "BINDINGS",
        "BOOTS",
        "CLOTHES",
        "PROTECTION",
        "ACCESSORIES",
        "OTHER"
    )

    override fun getAllProducts(
        request: GetAllProductsRequest,
        responseObserver: StreamObserver<GetAllProductsResponse>
    ) {
        logger.info("getAllProducts: Запрос всех товаров")
        
        val response = GetAllProductsResponse.newBuilder()
            .addAllProducts(products.values.toList())
            .build()

        responseObserver.onNext(response)
        responseObserver.onCompleted()
        
        logger.info("getAllProducts: Возвращено {} товаров", products.size)
    }

    override fun getProductById(
        request: GetProductByIdRequest,
        responseObserver: StreamObserver<GetProductByIdResponse>
    ) {
        logger.info("getProductById: Запрос товара с ID={}", request.productId)
        
        val product = products[request.productId]
        
        val response = if (product != null) {
            logger.info("getProductById: Товар найден: {}", product.title)
            GetProductByIdResponse.newBuilder()
                .setProduct(product)
                .setFound(true)
                .build()
        } else {
            logger.warn("getProductById: Товар с ID={} не найден", request.productId)
            GetProductByIdResponse.newBuilder()
                .setFound(false)
                .build()
        }

        responseObserver.onNext(response)
        responseObserver.onCompleted()
    }

    override fun getProductsByCategory(
        request: GetProductsByCategoryRequest,
        responseObserver: StreamObserver<GetProductsByCategoryResponse>
    ) {
        logger.info("getProductsByCategory: Запрос товаров категории={}", request.category)
        
        val filteredProducts = products.values.filter { 
            it.category.equals(request.category, ignoreCase = true) 
        }

        val response = GetProductsByCategoryResponse.newBuilder()
            .addAllProducts(filteredProducts)
            .build()

        responseObserver.onNext(response)
        responseObserver.onCompleted()
        
        logger.info("getProductsByCategory: Найдено {} товаров в категории {}", 
            filteredProducts.size, request.category)
    }

    override fun getAllCategories(
        request: GetAllCategoriesRequest,
        responseObserver: StreamObserver<GetAllCategoriesResponse>
    ) {
        logger.info("getAllCategories: Запрос всех категорий")
        
        val response = GetAllCategoriesResponse.newBuilder()
            .addAllCategories(categories)
            .build()

        responseObserver.onNext(response)
        responseObserver.onCompleted()
        
        logger.info("getAllCategories: Возвращено {} категорий", categories.size)
    }

    override fun validateProductExists(
        request: ValidateProductExistsRequest,
        responseObserver: StreamObserver<ValidateProductExistsResponse>
    ) {
        logger.info("validateProductExists: Валидация существования товара ID={}", request.productId)
        
        val exists = products.containsKey(request.productId)
        
        val response = ValidateProductExistsResponse.newBuilder()
            .setExists(exists)
            .build()

        responseObserver.onNext(response)
        responseObserver.onCompleted()
        
        logger.info("validateProductExists: Товар ID={} существует={}", request.productId, exists)
    }

    override fun validateProductPrice(
        request: ValidateProductPriceRequest,
        responseObserver: StreamObserver<ValidateProductPriceResponse>
    ) {
        logger.info("validateProductPrice: Валидация цены товара ID={}, ожидаемая цена={}", 
            request.productId, request.expectedPrice)
        
        val product = products[request.productId]
        
        val response = if (product != null) {
            val isValid = product.price == request.expectedPrice
            logger.info("validateProductPrice: Фактическая цена={}, валидно={}", product.price, isValid)
            ValidateProductPriceResponse.newBuilder()
                .setValid(isValid)
                .setActualPrice(product.price)
                .build()
        } else {
            logger.warn("validateProductPrice: Товар ID={} не найден для валидации цены", request.productId)
            ValidateProductPriceResponse.newBuilder()
                .setValid(false)
                .setActualPrice(0.0)
                .build()
        }

        responseObserver.onNext(response)
        responseObserver.onCompleted()
    }
}
