from __future__ import annotations

import uuid

import grpc

from . import travel_agency_pb2, travel_agency_pb2_grpc
from .grpc_status import extract_trace_id_from_rpc_error


class Lab4CLI:
    def __init__(
        self,
        core_target: str = "127.0.0.1:50051",
        reference_target: str = "127.0.0.1:50052",
    ) -> None:
        self._core_channel = grpc.insecure_channel(core_target)
        self._reference_channel = grpc.insecure_channel(reference_target)
        self._core_stub = travel_agency_pb2_grpc.CoreServiceStub(self._core_channel)
        self._reference_stub = travel_agency_pb2_grpc.ReferenceServiceStub(self._reference_channel)

    def run(self) -> None:
        actions = {
            "1": self._show_tours,
            "2": self._show_clients,
            "3": self._register_client,
            "4": self._create_booking,
            "5": self._show_bookings,
            "6": self._start_processing,
            "7": self._mark_ready,
            "8": self._record_payment,
            "9": self._issue_booking,
            "10": self._cancel_booking,
            "11": self._show_marketing_report,
            "0": self._exit_program,
        }

        while True:
            self._print_menu()
            choice = input("Выберите пункт меню: ").strip()
            action = actions.get(choice)
            if action is None:
                print("Неизвестная команда\n")
                continue
            action()

    def _print_menu(self) -> None:

        print("1. Показать туры")
        print("2. Показать клиентов")
        print("3. Зарегистрировать клиента")
        print("4. Создать бронирование")
        print("5. Показать бронирования")
        print("6. Перевести бронь в работу")
        print("7. Отметить бронь готовой")
        print("8. Провести оплату")
        print("9. Выдать бронь")
        print("10. Отменить бронь")
        print("11. Показать маркетинговый отчет")
        print("0. Выход")

    def _show_tours(self) -> None:
        response = self._call_rpc(
            self._reference_stub.ListTours,
            travel_agency_pb2.Empty(),
        )
        if response is None:
            return
        print()
        for tour in response.tours:
            print(
                f"[{tour.tour_id}] {tour.title}, {tour.destination}, {tour.days} дн., "
                f"{tour.base_price} руб., мест: {tour.available_seats}"
            )
        print()

    def _show_clients(self) -> None:
        response = self._call_rpc(
            self._reference_stub.ListClients,
            travel_agency_pb2.Empty(),
        )
        if response is None:
            return
        print()
        for client in response.clients:
            print(f"[{client.client_id}] {client.full_name}, статус: {client.loyalty_level}")
        print()

    def _register_client(self) -> None:
        full_name = input("Введите ФИО клиента: ").strip()
        loyalty_level = input(
            "Введите статус клиента (standard/silver/gold), по умолчанию standard: "
        ).strip() or "standard"
        response = self._call_rpc(
            self._reference_stub.RegisterClient,
            travel_agency_pb2.RegisterClientRequest(
                full_name=full_name,
                loyalty_level=loyalty_level,
            ),
        )
        if response is None:
            return
        self._print_status(response.success, response.message, response.trace_id)

    def _create_booking(self) -> None:
        response = self._call_rpc(
            self._core_stub.CreateBooking,
            travel_agency_pb2.CreateBookingRequest(
                client_id=self._read_int("Введите ID клиента: "),
                tour_id=self._read_int("Введите ID тура: "),
                travelers_count=self._read_int("Введите количество путешественников: "),
                amount_paid=input("Введите сумму предоплаты, по умолчанию 0: ").strip() or "0",
                hold_days=self._read_int("Введите срок брони в днях, по умолчанию 3: ", default=3),
            ),
        )
        if response is None:
            return
        self._print_status(response.success, response.message, response.trace_id)
        if response.success:
            print(
                f"Бронь {response.booking.booking_id}: {response.booking.total_price} руб., "
                f"статус {response.booking.status_label}\n"
            )

    def _show_bookings(self) -> None:
        response = self._call_rpc(
            self._core_stub.ListBookings,
            travel_agency_pb2.Empty(),
        )
        if response is None:
            return
        print()
        for booking in response.bookings:
            print(
                f"[{booking.booking_id}] {booking.client_name} -> {booking.tour_title} | "
                f"чел.: {booking.travelers_count} | сумма: {booking.total_price} руб. | "
                f"остаток: {booking.outstanding_balance} руб. | статус: {booking.status}"
            )
        print()

    def _start_processing(self) -> None:
        self._run_booking_transition("StartBookingProcessing", self._core_stub.StartBookingProcessing)

    def _mark_ready(self) -> None:
        self._run_booking_transition("MarkBookingReady", self._core_stub.MarkBookingReady)

    def _issue_booking(self) -> None:
        self._run_booking_transition("IssueBooking", self._core_stub.IssueBooking)

    def _cancel_booking(self) -> None:
        self._run_booking_transition("CancelBooking", self._core_stub.CancelBooking)

    def _record_payment(self) -> None:
        response = self._call_rpc(
            self._core_stub.RecordPayment,
            travel_agency_pb2.PaymentRequest(
                booking_id=self._read_int("Введите ID брони: "),
                amount=input("Введите сумму оплаты: ").strip(),
            ),
        )
        if response is None:
            return
        self._print_status(response.success, response.message, response.trace_id)

    def _show_marketing_report(self) -> None:
        response = self._call_rpc(
            self._core_stub.RenderMarketingReport,
            travel_agency_pb2.Empty(),
        )
        if response is None:
            return
        print()
        print(response.text)
        print()

    def _run_booking_transition(self, name: str, rpc) -> None:
        del name
        response = self._call_rpc(
            rpc,
            travel_agency_pb2.BookingIdRequest(
                booking_id=self._read_int("Введите ID брони: "),
            ),
        )
        if response is None:
            return
        self._print_status(response.success, response.message, response.trace_id)

    def _exit_program(self) -> None:
        self._core_channel.close()
        self._reference_channel.close()
        raise SystemExit

    def _metadata(self) -> list[tuple[str, str]]:
        return [("trace-id", uuid.uuid4().hex)]

    def _call_rpc(self, rpc, request):
        try:
            return rpc(request, metadata=self._metadata())
        except grpc.RpcError as error:
            self._print_rpc_error(error)
            return None

    def _print_status(self, success: bool, message: str, trace_id: str) -> None:
        prefix = "OK" if success else "Ошибка"
        print(f"{prefix}: {message} [trace_id={trace_id}]\n")

    def _print_rpc_error(self, error: grpc.RpcError) -> None:
        trace_id = extract_trace_id_from_rpc_error(error) or "-"
        print(
            f"Ошибка gRPC ({error.code().name}): {error.details()} "
            f"[trace_id={trace_id}]\n"
        )

    def _read_int(self, prompt: str, default: int | None = None) -> int:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        return int(raw)


def run_lab4_cli(
    core_target: str = "127.0.0.1:50051",
    reference_target: str = "127.0.0.1:50052",
) -> None:
    Lab4CLI(core_target=core_target, reference_target=reference_target).run()
