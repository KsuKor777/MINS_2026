package ru.iu3.infrastructure.generator

import ru.iu3.application.generator.IdGenerator
import java.util.UUID

internal class UuidGenerator : IdGenerator {

    override fun newId(): String = UUID.randomUUID().toString()
}