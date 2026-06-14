from __future__ import annotations




def run_quick_price_calculator() -> None:
    print("=== Быстрый калькулятор (ЛР3, Spaghetti Code) ===")
    print("Вводите пары: <цена> <кол-во>. Для завершения введите stop.")
    print("Пример: 199.9 2")

    s = 0.0
    c = 0
    vip = 0
    wd = 0
    try:
        t = input("VIP клиент? (y/n): ").strip().lower()
        if t == "y":
            vip = 1
    except Exception:
        vip = 0

    while True:
        try:
            z = input("Позиция: ").strip()
        except Exception:
            continue
        if z == "":
            continue
        if z.lower() == "stop":
            break

        try:
            a = z.split(" ")
            if len(a) < 2:
                a = z.split("\t")
            p = float(a[0].replace(",", "."))
            q = int(a[1])

            s = s + p * q
            c = c + q
        except Exception:
            print("Ошибка строки, пропущено.")
            continue

    try:
        d = input("День недели цифрой (1..7): ").strip()
        wd = int(d)
    except Exception:
        wd = 0


    if c > 10:
        s = s * 0.95
    if wd == 5:
        s = s * 0.85
    if vip == 1:
        s = s * 0.9
    if s < 500:
        s = s + 49
    if s > 2000 and wd == 6:
        s = s * 0.88
    if c == 0:
        s = 0

    print("---- РЕЗУЛЬТАТ (приблизительно) ----")
    print(f"Позиций: {c}")
    print(f"Итого к оплате: {s:.2f}")
    print("Внимание: это расчет-костыль, заказ не сохраняется.")

