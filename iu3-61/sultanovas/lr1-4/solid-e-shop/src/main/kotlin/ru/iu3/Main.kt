package ru.iu3

import ru.iu3.di.AppFactory
import ru.iu3.presentation.console.ConsoleApp

fun main() {

    val deps = AppFactory.createConsoleDeps()
    val userId = "u1"

    ConsoleApp(deps = deps, userId = userId).run()
}