from __future__ import annotations

from cafe_app.exceptions import (
    CafeError,
    ValidationError,
)
from cafe_app.commands import CommandBus, CreateCategoryCommand, CreateMenuItemCommand
from cafe_app.discounts import DiscountFactory
from cafe_app.observer import InMemoryOrderLogObserver, OrderEventPublisher
from cafe_app.payment import PaymentFactory
from cafe_app.quick_calc_spaghetti import run_quick_price_calculator
from cafe_app.receipt import ReceiptService
from cafe_app.repositories import InMemoryMenuRepository, InMemoryOrderRepository
from cafe_app.services import CheckoutService, MenuService, OrderService


def ask_int(prompt: str) -> int: #безопасно вводит номер стола, id стола и блюда, количество
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError as e:
        raise ValidationError("Ожидается целое число.") from e
    return value


def ask_str(prompt: str) -> str: #прочитать текст и убрать пробелы
    return input(prompt).strip()


def ask_payment_method(prompt: str) -> str:#Чтение способа оплаты
    return ask_str(prompt).lower()#приводит к нижнему ркгистру


def main() -> None:
    menu_repo = InMemoryMenuRepository() #хранит меню
    order_repo = InMemoryOrderRepository() #хранит заказы

    events = OrderEventPublisher()
    log_observer = InMemoryOrderLogObserver()
    events.subscribe(log_observer)

    menu_service = MenuService(repo=menu_repo) #создаёт категорию, добавялет блюдо, показывает меню
    command_bus = CommandBus()
    order_service = OrderService(menu_repo=menu_repo, order_repo=order_repo, publisher=events) #работает с заказами
    checkout_service = CheckoutService( #работает с оплатой
        order_repo=order_repo,
        payment_factory=PaymentFactory(),
        receipt_service=ReceiptService(),
        discount_factory=DiscountFactory(),
        publisher=events,
    )

    while True:
        print("\n=== Кафе (вариант 10) ===")
        print("1. Добавить категорию")
        print("2. Добавить блюдо")
        print("3. Показать меню")
        print("4. Открыть заказ на столе")
        print("5. Добавить блюдо в заказ (по столу)")
        print("6. Показать текущий заказ (по столу)")
        print("7. Оплатить заказ и распечатать чек (по столу)")
        print("8. Показать журнал событий заказа (Observer)")
        print("9. Показать историю команд (Command)")
        print("10. Быстрый калькулятор (ЛР3, Spaghetti Code)")
        print("0. Выход")

        choice = ask_str("Выберите пункт: ")

        try:
            if choice == "1":
                name = ask_str("Название категории: ")
                category = command_bus.execute(CreateCategoryCommand(menu_service=menu_service, name=name))
                print(f"Категория создана: [{category.id}] {category.name}")

            elif choice == "2":
                category_id = ask_int("ID категории: ")
                name = ask_str("Название блюда: ")
                price_text = ask_str("Цена (например 199.50): ")
                item = command_bus.execute(
                    CreateMenuItemCommand(
                        menu_service=menu_service,
                        category_id=category_id,
                        name=name,
                        price_text=price_text,
                    )
                )
                print(f"Блюдо создано: [{item.id}] {item.name} = {item.price:.2f}")

            elif choice == "3":
                print(menu_service.show_menu())

            elif choice == "4":
                table_number = ask_int("Номер стола: ")
                order = order_service.start_order(table_number=table_number)
                print(f"Открыт заказ: №{order.id} для стола {order.table_number}")

            elif choice == "5":
                table_number = ask_int("Номер стола: ")
                order = order_service.get_open_order_by_table(table_number)
                item_id = ask_int("ID блюда: ")
                quantity = ask_int("Количество: ")
                order_service.add_item_to_order(order_id=order.id, item_id=item_id, quantity=quantity)
                print("Блюдо добавлено.")

            elif choice == "6":
                table_number = ask_int("Номер стола: ")
                order = order_service.get_open_order_by_table(table_number)
                print(order_service.show_order_text(order_id=order.id))

            elif choice == "7":
                table_number = ask_int("Номер стола: ")
                order = order_service.get_open_order_by_table(table_number)
                method = ask_payment_method("Способ оплаты (cash/card/online): ")
                print("Тип скидки: none / student / happy")
                discount_key = ask_str("Введите скидку: ").lower()
                receipt_text = checkout_service.checkout(
                    order_id=order.id,
                    payment_method_key=method,
                    discount_key=discount_key,
                )
                print(receipt_text)

            elif choice == "8":
                if not log_observer.events:
                    print("Журнал событий пуст.")
                else:
                    print("=== События ===")
                    for event in log_observer.events:
                        print(event)

            elif choice == "9":
                if not command_bus.history:
                    print("История команд пуста.")
                else:
                    print("=== История команд ===")
                    for cmd_name in command_bus.history:
                        print(cmd_name)

            elif choice == "10":
                run_quick_price_calculator()

            elif choice == "0":
                print("Выход.")
                return

            else:
                raise ValidationError("Неизвестный пункт меню.")

        except CafeError as e: #ловит собственные ошибки (блюдо не найдено...)
            print(f"Ошибка: {e}")
        except ValueError as e: #ловит обычные ошибки типо неправильное число
            print(f"Некорректные данные: {e}")


if __name__ == "__main__":
    main()

