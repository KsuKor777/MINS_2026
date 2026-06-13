import com.google.protobuf.gradle.id

plugins {
    `java-library`
    id("com.google.protobuf") version "0.9.4"
}

group = "ru.iu3"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    api("io.grpc:grpc-protobuf:1.59.0")
    api("io.grpc:grpc-stub:1.59.0")
    api("io.grpc:grpc-api:1.59.0")
    implementation("io.grpc:grpc-netty-shaded:1.59.0")

    compileOnly("org.apache.tomcat:annotations-api:6.0.53")
}

protobuf {
    protoc {
        artifact = "com.google.protobuf:protoc:3.25.1"
    }
    plugins {
        id("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:1.59.0"
        }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins {
                id("grpc")
            }
        }
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
