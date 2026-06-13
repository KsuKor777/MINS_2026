package ru.iu3.domain.repository

import ru.iu3.domain.model.Cart

internal interface CartRepository {

    fun get(): Cart

    fun clear()
}