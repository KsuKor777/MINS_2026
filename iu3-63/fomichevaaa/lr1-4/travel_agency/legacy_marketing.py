from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal

from .repositories import BookingRepository, ClientRepository, TourRepository


class LegacyMarketingHub:

    def __init__(
        self,
        booking_repository: BookingRepository,
        client_repository: ClientRepository,
        tour_repository: TourRepository,
    ) -> None:
        self._booking_repository = booking_repository
        self._client_repository = client_repository
        self._tour_repository = tour_repository 
        self._last_reference_date: date | None = None                                                                            #атрибут для кеширования даты последнего отчета: нужно ли пересоздавать отчет
        self._last_rows: list[dict[str, object]] = []                                                                            #атрибут для хранения последних сгенерированных строк отчёта
                                                                                                                                 #Каждый словарь представляет данные одного клиента из отчёта (результат build_personal_offer). 
                                                                                                                                 #Используется для быстрого формирования суммарной статистики без пересчёта.
    def build_personal_offer(
        self,
        client_id: int,
        reference_date: date | None = None,
    ) -> dict[str, object]:
        current_date = reference_date or date.today()
        client = self._client_repository.get_by_id(client_id)
        bookings = []
        total_spend = Decimal("0.00")
        total_debt = Decimal("0.00")
        active_bookings = 0
        issued_bookings = 0
        cancelled_bookings = 0
        nearest_deadline_days: int | None = None
        destinations = Counter()

        for booking in self._booking_repository.list_all():
            if booking.client_id != client.client_id:
                continue

            bookings.append(booking)
            total_spend += booking.total_price
            total_debt += booking.outstanding_balance

            if booking.state.is_active():
                active_bookings += 1
            if booking.status == "issued":
                issued_bookings += 1
            if booking.status == "cancelled":
                cancelled_bookings += 1

            booking_tour = self._tour_repository.get_by_id(booking.tour_id)
            destinations[booking_tour.destination] += 1

            days_left = (booking.hold_until - current_date).days
            if nearest_deadline_days is None or days_left < nearest_deadline_days:
                nearest_deadline_days = days_left

        segment = "cross_sell"
        discount_rate = Decimal("0.04")
        channel = "email"

        if not bookings:
            segment = "welcome"
            discount_rate = Decimal("0.03")
            channel = "push"
        elif total_debt > Decimal("0.00") and nearest_deadline_days is not None and nearest_deadline_days <= 2:
            segment = "reactivation"
            discount_rate = Decimal("0.05")
            channel = "sms"
        elif client.loyalty_level == "gold" or total_spend >= Decimal("90000"):
            segment = "vip"
            discount_rate = Decimal("0.12")
            channel = "personal_manager"
        elif cancelled_bookings > 0 and issued_bookings == 0:
            segment = "winback"
            discount_rate = Decimal("0.07")
            channel = "email"
        elif active_bookings == 0:
            segment = "weekend"
            discount_rate = Decimal("0.06")
            channel = "push"

        recommended_tour = "-"
        favorite_destination = "-"
        tours = self._tour_repository.list_all()

        if destinations:
            favorite_destination = destinations.most_common(1)[0][0]
            for tour in tours:
                if tour.destination == favorite_destination and tour.available_seats > 0:
                    recommended_tour = tour.title
                    break

        if recommended_tour == "-":
            for tour in sorted(tours, key=lambda item: (item.base_price, item.title)):
                if tour.available_seats > 0:
                    recommended_tour = tour.title
                    if favorite_destination == "-":
                        favorite_destination = tour.destination
                    break

        priority_score = 10
        priority_score += active_bookings * 8
        priority_score += issued_bookings * 5
        priority_score += int(total_spend / Decimal("10000"))
        priority_score += int(total_debt / Decimal("5000"))
        if client.loyalty_level == "gold":
            priority_score += 20
        elif client.loyalty_level == "silver":
            priority_score += 10
        if nearest_deadline_days is not None and nearest_deadline_days <= 2:
            priority_score += 25
        if segment == "welcome":
            priority_score -= 15
        if segment == "weekend":
            priority_score -= 5

        discount_percent = int(discount_rate * Decimal("100"))
        promo_code = f"{segment[:3].upper()}{client.client_id}{priority_score}"
        message = (
            f"{client.full_name}: канал={channel}, сегмент={segment}, "
            f"тур={recommended_tour}, направление={favorite_destination}, "
            f"скидка={discount_percent}%, долг={total_debt}, промокод={promo_code}"
        )

        return {
            "client_id": client.client_id,
            "client_name": client.full_name,
            "segment": segment,
            "channel": channel,
            "discount_rate": discount_rate,
            "recommended_tour": recommended_tour,
            "favorite_destination": favorite_destination,
            "priority_score": priority_score,
            "bookings_count": len(bookings),
            "active_bookings": active_bookings,
            "total_spend": total_spend,
            "total_debt": total_debt,
            "message": message,
        }

    def build_campaign_report(self, reference_date: date | None = None) -> list[str]:
        current_date = reference_date or date.today()
        self._last_reference_date = current_date
        self._last_rows = []

        for client in self._client_repository.list_all():
            self._last_rows.append(self.build_personal_offer(client.client_id, current_date))

        self._last_rows.sort(
            key=lambda row: (int(row["priority_score"]), str(row["client_name"])),
            reverse=True,
        )

        report = [f"Маркетинговая кампания на {current_date.isoformat()}:"]
        if not self._last_rows:
            report.append("Клиентов для анализа нет.")
            report.append(self.build_summary(current_date))
            return report

        for row in self._last_rows:
            report.append(
                f"[{row['client_id']}] {row['message']} | активных броней={row['active_bookings']} "
                f"| всего броней={row['bookings_count']} | приоритет={row['priority_score']}"
            )

        report.append(self.build_summary(current_date))
        return report

    def build_summary(self, reference_date: date | None = None) -> str:
        current_date = reference_date or date.today()
        if self._last_reference_date != current_date:
            self.build_campaign_report(current_date)

        segment_counts = Counter()
        channel_counts = Counter()
        total_debt = Decimal("0.00")
        total_spend = Decimal("0.00")
        hottest_client = "-"

        if self._last_rows:
            hottest_client = str(self._last_rows[0]["client_name"])

        for row in self._last_rows:
            segment_counts[str(row["segment"])] += 1
            channel_counts[str(row["channel"])] += 1
            total_debt += Decimal(str(row["total_debt"]))
            total_spend += Decimal(str(row["total_spend"]))

        return (
            "Итог кампании: "
            f"клиентов={len(self._last_rows)}, "
            f"сегменты={dict(segment_counts)}, "
            f"каналы={dict(channel_counts)}, "
            f"общая выручка={total_spend}, "
            f"общий долг={total_debt}, "
            f"приоритетный клиент={hottest_client}"
        )

    def render_cli_report(self, reference_date: date | None = None) -> str:
        return "\n".join(self.build_campaign_report(reference_date))
