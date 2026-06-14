from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from .discounts import DiscountFactory
from .entities import OrderLine
from .observer import OrderEventPublisher
from .payment import PaymentFactory
from .receipt import ReceiptService
from .repositories import InMemoryMenuRepository, InMemoryOrderRepository
from .utils import parse_money


@dataclass
class MenuService: #работа с меню
    repo: InMemoryMenuRepository #репозиторий меню, метсо хранения

    def create_category(self, name: str): #создает категорию меню
        return self.repo.add_category(name) #получает название категории и передает ее в репозиторий

    def create_item(self, category_id: int, name: str, price_text: str):
        price = parse_money(price_text) #текст превращается в денежный тип
        return self.repo.add_item(category_id=category_id, name=name, price=price) #сервис передает в репохиторий, репозиторий проверяет есть ли такая категория, пустое ли название, положит ли цена

    def show_menu(self) -> str: #формирует текст меню
        cats = self.repo.list_categories() #Берем все категории их репозитория и получае  список объектов
        items = {c.id: self.repo.list_items(c.id) for c in cats} #создает словарь (ключ=айди категории, значение = список блюд в этой категории)
        lines: list[str] = [] #создается пустой список строк
        lines.append("====== МЕНЮ ======")
        for c in cats: #проходит по всем категориям
            lines.append(f"[{c.id}] {c.name}") #вывод номера категории и ей имя
            for it in items[c.id]: #для текущей категории берутся все блюда
                lines.append(f"  - [{it.id}] {it.name}: {it.price:.2f}")
        lines.append("====================")
        return "\n".join(lines) #берет список строк, соединяет их в текст через переносы строки


@dataclass
class OrderService:
    menu_repo: InMemoryMenuRepository #чтобы получать блюда
    order_repo: InMemoryOrderRepository #чтобы работать с заказами
    publisher: OrderEventPublisher | None = None

    def start_order(self, table_number: int): #открывает новый заказ на указанный стол
        order = self.order_repo.create_order(table_number=table_number) #репозиторий проверяет номер стола, проверяет нет ли уже открытого заказа, создает ордер)
        if self.publisher:
            self.publisher.notify("ORDER_OPENED", order)
        return order

    def get_open_order_by_table(self, table_number: int): #ищет открытый заказ по номеру стола
        return self.order_repo.get_open_order_by_table(table_number)

    def add_item_to_order(self, order_id: int, item_id: int, quantity: int = 1): #добавить блюдо в заказ, аргументы - в какой заказ добавляем, какое блюдо добавляем, сколько штук
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным.")
        item = self.menu_repo.get_item(item_id) #по item_id из меню достается конкретное блюдо
        line = OrderLine( #одна строка заказа
            item_id=item.id,#айди
            item_name=item.name, #имя блюда
            unit_price=item.price, #цена
            quantity=quantity, #кол-во
        )
        self.order_repo.add_line(order_id=order_id, line=line) #готовая строка передается в репозиторий
        if self.publisher:
            order = self.order_repo.get_order(order_id)
            self.publisher.notify("ITEM_ADDED", order)

    def show_order_text(self, order_id: int) -> str:
        order = self.order_repo.get_order(order_id) #получаем заказ по айди
        lines: list[str] = []
        lines.append("====== ТЕКУЩИЙ ЗАКАЗ ======")
        lines.append(f"Заказ №: {order.id} | Стол: {order.table_number} | Статус: {order.status}") #номер заказа, номер стола, статус заказа
        lines.append("------------------------------------")
        if not order.lines: #если позиции есть, то программа проходит по каждой из них
            lines.append("(пусто)")
        for ln in order.lines:
            lines.append(f"{ln.quantity} x {ln.item_name} @ {ln.unit_price:.2f} = {ln.line_total:.2f}") #сумма за эту позицию
        lines.append("------------------------------------")
        lines.append(f"Сумма: {order.total_amount():.2f}") #складывает суммы всех строк заказа
        lines.append("===============================")
        return "\n".join(lines)


@dataclass
class CheckoutService: #оплата и чек
    order_repo: InMemoryOrderRepository #получить и закрыть заказ
    payment_factory: PaymentFactory #выбрать способ оплаты
    receipt_service: ReceiptService #сделать чек
    discount_factory: DiscountFactory
    publisher: OrderEventPublisher | None = None

    def checkout(self, order_id: int, payment_method_key: str, discount_key: str = "none") -> str: #order_id какой заказ оплачиваем, payment_method_key чем оплачиваем
        processor = self.payment_factory.get_processor(payment_method_key)
        order = self.order_repo.get_order(order_id) #находит сам заказ
        original_total = order.total_amount() #считается общая сумма
        strategy = self.discount_factory.get_strategy(discount_key)
        discounted_total = strategy.apply(original_total)
        payment = processor.pay(discounted_total) #выбранный обработчик оплаты получает сумму и проводит оплату
        paid_at = datetime.now() #фиксирует текущее время
        self.order_repo.mark_paid(order_id=order_id, payment_method=payment.method_name, paid_at=paid_at) #репозиторий проверяет, что заказ открыт, меняет статус на закрыт, записывает спосб оплаты, записывает время оплаты
        if self.publisher:
            closed_order = self.order_repo.get_order(order_id)
            self.publisher.notify("ORDER_PAID", closed_order)
        return self.receipt_service.generate_receipt_text(
            order=order,
            payment=payment,
            original_total=original_total,
            discounted_total=discounted_total,
            discount_name=strategy.name,
        ) #возвращает готовый чек

