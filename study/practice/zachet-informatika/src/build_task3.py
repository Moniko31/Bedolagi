"""Задание 3, шаг 1: лист «Заказы» из PDF-данных + копии «Камилла» (сортировка)
и «Аджиева» (автофильтр). Сводную таблицу добавляет add_pivot.py через LibreOffice."""
import sys
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.filters import CustomFilter, CustomFilters, FilterColumn, Filters

SRC = Path(__file__).parent
OUT = sys.argv[1]
NAME, SURNAME = "Камилла", "Аджиева"
LETTER = NAME[0]          # «К»
DELIVERY = 8              # последняя цифра логина

REGION = {
    "Уфа": "Башкирия", "Белгород": "Белгородская обл.", "Брянск": "Брянская обл.",
    "Владимир": "Владимирская обл.", "Волгоград": "Волгоградская обл.",
    "Новохоперск": "Волгоградская обл.", "Урюпинск": "Волгоградская обл.",
    "Весьегонск": "Вологодская обл.", "Моршанск": "Воронежская обл.",
    "Калининград": "Калининградская обл.", "Серпухов": "Калужская обл.", "Калуга": "Калужская обл.",
    "Анапа": "Краснодарский край", "Краснодар": "Краснодарский край", "Курск": "Курская обл.",
    "Всеволжск": "Ленинградская обл.", "Выборг": "Ленинградская обл.",
    "Санкт-Петербург": "Ленинградская обл.", "Липецк": "Липецкая обл.", "Магадан": "Магаданская обл.",
    "Болшево": "Московская обл.", "Дедовск": "Московская обл.", "Долгопрудный": "Московская обл.",
    "Люберцы": "Московская обл.", "Москва": "Московская обл.", "Мытищи": "Московская обл.",
    "Солнечногорск": "Московская обл.", "Электросталь": "Московская обл.", "Фрязино": "Московская обл.",
    "Мурманск": "Мурманская обл.", "Валдай": "Новгородская обл.", "Вышний Волочек": "Новгородская обл.",
    "Новгород": "Новгородская обл.", "Ачинск": "Новосибирская обл.", "Новосибирск": "Новосибирская обл.",
    "Омск": "Омская обл.", "Оренбург": "Оренбургская обл.", "Орел": "Орловская обл.",
    "Остров": "Псковская обл.", "Псков": "Псковская обл.", "Мариуполь": "Ростовская обл.",
    "Шахты": "Ростовская обл.", "Рязань": "Рязанская обл.", "Саратов": "Саратовская обл.",
    "Екатеринбург": "Свердловская обл.", "Казань": "Татарстан", "Тула": "Тульская губерния",
    "Беркакит": "Хабаровский край", "Тында": "Хабаровский край",
}
# Исключения из справочника клиентов (так в исходной таблице)
OVERRIDE = {
    "10000": ('Кафе "Райские Кущи"', "пр-д Детей Лейтенанта Шмидта, 23"),
    "10106": ('Универмаг "Анна"', "Центральная, 23"),
}


def lines(name):
    return [l.strip() for l in (SRC / name).read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


clients = {c: (n, a) for c, n, a in (l.split("|") for l in lines("clients.txt"))}
orders = [l.split() for l in lines("orders.txt")]
sums = [t for l in lines("sums.txt") for t in l.split()]

geo, city = [], None
for l in lines("geo.txt"):
    t = l.split()
    idx, dlv, d = t[0], int(t[1]), t[2:11]
    city = " ".join(t[11:]) or city
    dates = [datetime.strptime(" ".join(d[i:i + 3]), "%d %b %y") for i in (0, 3, 6)]
    geo.append((city, REGION[city], idx, dlv, *dates))

assert len(orders) == len(geo) == len(sums) == 1000

rows = []
for (num, cl, emp), g, s in zip(orders, geo, sums):
    name, addr = OVERRIDE.get(num, clients[cl])
    rows.append([int(num), cl, int(emp), name, addr, *g, None if s == "_" else float(s)])

HEAD = ["Заказ", "Клиент", "Сотрудник", "Название получателя", "Адрес получателя",
        "Город получателя", "Регион получателя", "Индекс получателя", "Доставка",
        "Дата размещения", "Дата назначения", "Дата исполнения", "Сумма доставки"]
WIDTH = [8, 9, 6, 30, 30, 16, 21, 9, 7, 12, 12, 12, 10]

thin = Side(style="thin")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
head_fill = PatternFill("solid", fgColor="FDE9D9")
font = Font(name="Arial", size=10)
bold = Font(name="Arial", size=10, bold=True)


def fill_sheet(ws, data):
    ws.append(HEAD)
    for c in ws[1]:
        c.font, c.fill, c.border = bold, head_fill, box
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 42
    for r in data:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font, c.border = font, box
        for c in row[9:12]:
            c.number_format = "d mmm yy"
        row[7].number_format = "@"
    for i, w in enumerate(WIDTH, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = "A2"


wb = Workbook()
fill_sheet(wb.active, rows)
wb.active.title = "Заказы"

# 3.1 + 3.2: лист с именем — сортировка Регион ↑, Сумма доставки ↓, Сотрудник ↑
srt = sorted(rows, key=lambda r: (r[6], -(r[12] if r[12] is not None else float("-inf")), r[2]))
fill_sheet(wb.create_sheet(NAME), srt)

# 3.1 + 3.3: лист с фамилией — автофильтр: адрес начинается на «К», Доставка = 8
ws = wb.create_sheet(SURNAME)
fill_sheet(ws, rows)
ws.auto_filter.ref = f"A1:M{len(rows) + 1}"
ws.auto_filter.filterColumn.append(FilterColumn(
    colId=4, customFilters=CustomFilters(customFilter=[CustomFilter(operator="equal", val=f"{LETTER}*")])))
ws.auto_filter.filterColumn.append(FilterColumn(colId=8, filters=Filters(filter=[str(DELIVERY)])))
shown = 0
for i, r in enumerate(rows, start=2):
    ok = r[4].startswith(LETTER) and r[8] == DELIVERY
    ws.row_dimensions[i].hidden = not ok
    shown += ok
print("строк после фильтра:", shown)

wb.active = 1
wb.save(OUT)
print("saved", OUT)
