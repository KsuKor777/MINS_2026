plugins {
    kotlin("jvm") version "2.0.20"
    id("com.google.protobuf") version "0.9.4"
    application
}

group = "ru.iu3"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    implementation(project(":proto"))
    
    // gRPC
    implementation("io.grpc:grpc-protobuf:1.59.0")
    implementation("io.grpc:grpc-stub:1.59.0")
    implementation("io.grpc:grpc-netty-shaded:1.59.0")
    
    // Kotlin
    implementation(kotlin("stdlib"))
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    
    // Logging
    implementation("ch.qos.logback:logback-classic:1.4.14")
    implementation("net.logstash.logback:logstash-logback-encoder:7.4")
    
    // Annotations
    compileOnly("org.apache.tomcat:annotations-api:6.0.53")
}

protobuf {
    protoc {
        artifact = "com.google.protobuf:protoc:3.25.1"
    }
    plugins {
        create("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:1.59.0"
        }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins {
                create("grpc")
            }
        }
    }
}

application {
    mainClass.set("ru.iu3.servicea.CoreServiceApplicationKt")
}

tasks.test {
    useJUnitPlatform()
}

tasks.register<JavaExec>("runTestClient") {
    group = "application"
    description = "Запуск тестового клиента"
    mainClass.set("ru.iu3.servicea.TestClientKt")
    classpath = sourceSets["main"].runtimeClasspath
    standardInput = System.`in`
}

kotlin {
    jvmToolchain(17)
}
