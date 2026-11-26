"""Задание 3.4: сводная таблица на новом листе «Свод» через LibreOffice UNO.
Строки — Город получателя, столбцы — Сотрудник, значения — MAX(Сумма доставки).
Источник — лист с именем (Камилла).
Запуск: soffice --headless --accept="socket,host=localhost,port=2002;urp;" &
        python3 add_pivot.py in.xlsx out.xlsx"""
import sys, time, uno
from pathlib import Path
from com.sun.star.beans import PropertyValue
from com.sun.star.table import CellAddress, CellRangeAddress
from com.sun.star.sheet.DataPilotFieldOrientation import ROW, COLUMN, DATA
from com.sun.star.sheet.GeneralFunction import MAX


def prop(n, v):
    p = PropertyValue(); p.Name, p.Value = n, v; return p


src, dst = (Path(a).resolve() for a in sys.argv[1:3])
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(30):
    try:
        ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(src.as_uri(), "_blank", 0, (prop("Hidden", True),))

sheets = doc.Sheets
source = sheets.getByName("Камилла")
src_idx = list(sheets.ElementNames).index("Камилла")
sheets.insertNewByName("Свод", sheets.Count)
target = sheets.getByName("Свод")

cur = source.createCursor(); cur.gotoEndOfUsedArea(False)
rng = CellRangeAddress(); rng.Sheet = src_idx
rng.StartColumn, rng.StartRow, rng.EndColumn, rng.EndRow = 0, 0, cur.RangeAddress.EndColumn, cur.RangeAddress.EndRow

dp_tables = target.getDataPilotTables()
desc = dp_tables.createDataPilotDescriptor()
desc.setSourceRange(rng)
fields = desc.getDataPilotFields()
names = [fields.getByIndex(i).Name for i in range(fields.Count)]
fields.getByIndex(names.index("Город получателя")).Orientation = ROW
fields.getByIndex(names.index("Сотрудник")).Orientation = COLUMN
data = fields.getByIndex(names.index("Сумма доставки"))
data.Orientation = DATA
data.Function = MAX
desc.ShowFilterButton = False

dest = CellAddress(); dest.Sheet = list(sheets.ElementNames).index("Свод"); dest.Column, dest.Row = 0, 2
dp_tables.insertNewByName("Свод_доставка", dest, desc)
target.getCellByPosition(0, 0).String = "Максимальная сумма доставки по городам и сотрудникам"
target.getCellByPosition(0, 0).CharWeight = 150.0

doc.storeToURL(dst.as_uri(), (prop("FilterName", "Calc MS Excel 2007 XML"),))
doc.close(True)
print("saved", dst)
