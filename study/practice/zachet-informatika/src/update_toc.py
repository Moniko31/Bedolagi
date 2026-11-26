"""Обновляет оглавление и поля в docx через LibreOffice Writer (UNO) и пересохраняет в docx.
Шрифт 11 пт выставляется и для стилей оглавления."""
import sys, uno
from pathlib import Path
from com.sun.star.beans import PropertyValue


def prop(n, v):
    p = PropertyValue(); p.Name, p.Value = n, v; return p


src, dst = (Path(a).resolve() for a in sys.argv[1:3])
local = uno.getComponentContext()
ctx = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local) \
    .resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(src.as_uri(), "_blank", 0, (prop("Hidden", True),))

pstyles = doc.StyleFamilies.getByName("ParagraphStyles")
for name in pstyles.ElementNames:
    if name.startswith("Contents") or name.startswith("Content") or "TOC" in name:
        st = pstyles.getByName(name)
        st.CharHeight = 11.0
        st.CharFontName = "Times New Roman"

idx = doc.getDocumentIndexes()
print("indexes:", idx.Count)
for i in range(idx.Count):
    ix = idx.getByIndex(i)
    ix.Title = ""
    ix.update()
doc.getTextFields().refresh()
doc.refresh()
doc.storeToURL(dst.as_uri(), (prop("FilterName", "MS Word 2007 XML"),))
doc.close(True)
print("saved", dst)
