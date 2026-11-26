"""Задание 2: таблица оплаты труда (вариант 8: Премия 1 = 22 %, Премия 2 = 15 %)."""
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

OUT = sys.argv[1]
PREMIA1, PREMIA2 = 0.22, 0.15

thin = Side(style="thin")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
head_fill = PatternFill("solid", fgColor="DA9694")
bold = Font(name="Arial", bold=True, size=10)
norm = Font(name="Arial", size=10)
RUB = '#,##0.00"р."'

wb = Workbook()
ws = wb.active
ws.title = "Лист1"

# 2.1 Проценты премий
ws["E1"], ws["F1"] = "Премия1, %", "Премия2, %"
ws["E2"], ws["F2"] = PREMIA1, PREMIA2
for c in ("E1", "F1", "E2", "F2"):
    ws[c].border = box
    ws[c].font = bold if c.endswith("1") else norm
ws["E2"].number_format = ws["F2"].number_format = "0%"

headers = ["№", "Фамилия", "Базовая зар. плата, руб.", "Премия1, руб.", "Премия2, руб.", "Всего, руб."]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=6, column=col, value=h)
    c.font, c.fill, c.border = bold, head_fill, box
    c.alignment = Alignment(wrap_text=True, vertical="top")

staff = [("Иванов И.И.", 23000), ("Петров П.П.", 58500), ("Сидоров С.С.", 13000),
         ("Николаев Н.Н.", 25000), ("Сергеев С.С.", 30000), ("Александров А.А.", 42000),
         ("Владимиров В.В.", 95000), ("Максимов М.М.", 65000), ("Артемов А.А.", 9300),
         ("Ильин И.И.", 38500)]

for i, (name, salary) in enumerate(staff):
    r = 7 + i
    ws.cell(r, 1, i + 1)
    ws.cell(r, 2, name)
    ws.cell(r, 3, salary)
    ws.cell(r, 4, f"=C{r}*$E$2")       # 2.2 абсолютная ссылка на Премию 1
    ws.cell(r, 5, f"=C{r}*$F$2")       # 2.3 абсолютная ссылка на Премию 2
    ws.cell(r, 6, f"=C{r}+D{r}+E{r}")  # 2.4 зарплата с премиями
    for col in range(1, 7):
        c = ws.cell(r, col)
        c.border, c.font = box, norm
        if col >= 3:
            c.number_format = RUB

# 2.5 Итого
for col in range(1, 7):
    ws.cell(17, col).border = box
ws["E17"] = "Итого:"
ws["E17"].font = norm
ws["F17"] = "=SUM(F7:F16)"
ws["F17"].number_format = RUB
ws["F17"].font = bold

for col, w in zip("ABCDEF", (4, 20, 18, 16, 16, 18)):
    ws.column_dimensions[col].width = w
ws.row_dimensions[6].height = 28

wb.save(OUT)
print("saved", OUT)
