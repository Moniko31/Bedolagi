"""Тестовая деталь: фланец. Запуск через FreeCADCmd (без графики).

    FreeCAD.AppImage --console flange.py   (или FreeCADCmd flange.py)

Результат (рядом со скриптом): flange.FCStd, flange.step, flange.stl,
flange_front.dxf / flange_top.dxf (проекции), flange_drawing.svg (чертёж).
"""
import os
import math
import FreeCAD as App
import Part

OUT = os.path.dirname(os.path.abspath(__file__))

# --- Параметры, мм ---
D_OUT = 100.0     # внешний диаметр
D_HUB = 50.0      # диаметр ступицы
D_BORE = 30.0     # центральное отверстие
T_PLATE = 12.0    # толщина фланца
H_HUB = 25.0      # полная высота со ступицей
D_BOLT_CIRCLE = 75.0
D_BOLT = 9.0
N_BOLTS = 4

doc = App.newDocument("Flange")

plate = Part.makeCylinder(D_OUT / 2, T_PLATE)
hub = Part.makeCylinder(D_HUB / 2, H_HUB)
body = plate.fuse(hub)

body = body.cut(Part.makeCylinder(D_BORE / 2, H_HUB))
for i in range(N_BOLTS):
    a = 2 * math.pi * i / N_BOLTS + math.pi / 4
    pos = App.Vector(D_BOLT_CIRCLE / 2 * math.cos(a), D_BOLT_CIRCLE / 2 * math.sin(a), 0)
    body = body.cut(Part.makeCylinder(D_BOLT / 2, T_PLATE, pos))

body = body.removeSplitter()
obj = doc.addObject("Part::Feature", "Flange")
obj.Shape = body
doc.recompute()

print("Volume mm3:", round(body.Volume, 1), "Valid:", body.isValid())
bb = body.BoundBox
print("Size:", round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1))

doc.saveAs(os.path.join(OUT, "flange.FCStd"))
Part.export([obj], os.path.join(OUT, "flange.step"))

import Mesh
Mesh.export([obj], os.path.join(OUT, "flange.stl"))
print("EXPORT OK")
