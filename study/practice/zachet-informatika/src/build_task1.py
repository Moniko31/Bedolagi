"""Задание 1: документ «К заданию 1.docx» по тексту из PDF.
Заголовок 1 / Заголовок 2, таблица ассортимента фруктов, шрифт 11 пт, номера страниц,
поле оглавления в конце (заполняет update_toc.py через LibreOffice)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(sys.argv[1])
IMG = OUT.parent
FONT = "Times New Roman"
SIZE = Pt(11)
F = "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf"


def font(sz, bold=False):
    return ImageFont.truetype(F.format("Bold" if bold else "Regular"), sz)


def box(d, xy, text, fill, sz=22, bold=True, dashed=False, color="black"):
    x0, y0, x1, y1 = xy
    d.rectangle(xy, fill=fill, outline="#333", width=2)
    if dashed:
        d.rectangle(xy, fill=fill, outline=fill)
        for x in range(x0, x1, 12):
            d.line([(x, y0), (min(x + 6, x1), y0)], fill="#333", width=2)
            d.line([(x, y1), (min(x + 6, x1), y1)], fill="#333", width=2)
        for y in range(y0, y1, 12):
            d.line([(x0, y), (x0, min(y + 6, y1))], fill="#333", width=2)
            d.line([(x1, y), (x1, min(y + 6, y1))], fill="#333", width=2)
    d.multiline_text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font(sz, bold), fill=color,
                     anchor="mm", align="center", spacing=4)


def figure_1_1(path):
    im = Image.new("RGB", (1240, 1000), "white")
    d = ImageDraw.Draw(im)
    blue, light, yellow, pale = "#2F5BEA", "#99C9FF", "#FFC800", "#FFFF99"
    ln = dict(fill="#333", width=2)
    d.line([(630, 140), (330, 200)], **ln); d.line([(630, 140), (870, 200)], **ln)
    d.line([(330, 330), (330, 380)], **ln)
    for x in (130, 230, 330, 430, 520):
        d.line([(330, 490), (x, 560)], **ln)
    d.line([(150, 620), (150, 660)], **ln); d.line([(420, 620), (420, 660)], **ln)
    d.line([(870, 330), (690, 380)], **ln); d.line([(870, 330), (820, 530)], **ln)
    d.line([(870, 330), (1040, 380)], **ln)
    box(d, (300, 10, 960, 140), "Комплекс программных средств\nподдержки дистанционного обучения\n«Пегас»", blue, 30, color="white")
    box(d, (180, 200, 480, 330), "СДО\n«Пегас Портал»\npegas.bsu.edu.ru", blue, 28, color="white")
    box(d, (620, 200, 1140, 330), "Комплект инструментальных\nсредств\n«Пегас Инструменты»", blue, 28, color="white")
    box(d, (230, 380, 430, 490), "LMS\n«MOODLE»", yellow, 30)
    box(d, (40, 560, 270, 620), "Блок\n«Деканат»", pale, 20, False)
    box(d, (310, 560, 540, 620), "Блок\n«Сервис ЦДО»", pale, 20, False)
    box(d, (40, 660, 270, 710), "Блок «Школа»", pale, 20, False, dashed=True)
    box(d, (310, 660, 540, 760), "Блок\n«Электронная\nпочта»", pale, 20, False)
    box(d, (580, 380, 800, 470), "Проигрыватель\nУМК «Пегас\nКонтент Плейер»", light, 19, False)
    box(d, (950, 380, 1170, 560), "Конвертор\nдокументов из\nформата Microsoft\nWord в формат\nMoodle XML\n(«Пегас Конвертор»)", light, 18, False)
    box(d, (690, 530, 950, 680), "Программа\nгенерации\nархивных zip-\nфайлов («Пегас\nГенератор»)", light, 18, False)
    im.crop((0, 0, 1240, 780)).save(path)


def figure_1_2(path):
    im = Image.new("RGB", (420, 330), "white")
    d = ImageDraw.Draw(im)
    tree = [(0, "usr"), (1, "local"), (2, "Apache2"), (2, "mysql"), (2, "PHP"),
            (1, "wwwroot"), (2, "moodle"), (2, "moodledata"), (2, "phpMyAdmin")]
    for i, (lvl, name) in enumerate(tree):
        x, y = 20 + lvl * 40, 15 + i * 34
        d.rectangle((x + 22, y + 6, x + 46, y + 24), fill="#F7D774", outline="#B08A20")
        d.rectangle((x + 22, y + 3, x + 32, y + 7), fill="#F7D774", outline="#B08A20")
        if lvl < 2:
            d.rectangle((x, y + 8, x + 12, y + 20), outline="#777"); d.line((x + 3, y + 14, x + 9, y + 14), fill="#333")
        d.text((x + 54, y + 15), name, font=font(20), fill="black", anchor="lm")
    im.save(path)


def figure_1_3(path):
    im = Image.new("RGB", (900, 520), "#F2F2F2")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 899, 519), outline="#888", width=3)
    d.multiline_text((450, 260), "Рисунок 1.3\n(снимок экрана мастера установки Apache\n"
                     "из исходного документа — в PDF доступен только\nкак растровое изображение)",
                     font=font(26), fill="#555", anchor="mm", align="center", spacing=8)
    im.save(path)


def set_style_font(style, size=SIZE, bold=None):
    style.font.name = FONT
    style.font.size = size
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(attr), None)


def add_field(paragraph, instr, placeholder=""):
    run = paragraph.add_run()
    for tag, extra in (("w:fldChar", {"w:fldCharType": "begin", "w:dirty": "true"}),
                       ("w:instrText", None), ("w:fldChar", {"w:fldCharType": "separate"}),
                       ("w:t", None), ("w:fldChar", {"w:fldCharType": "end"})):
        el = OxmlElement(tag)
        if extra:
            for k, v in extra.items():
                el.set(qn(k), v)
        if tag == "w:instrText":
            el.set(qn("xml:space"), "preserve"); el.text = instr
        if tag == "w:t":
            el.text = placeholder
        run._r.append(el)


doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21)
sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)

normal = doc.styles["Normal"]
set_style_font(normal)
normal.paragraph_format.first_line_indent = Cm(1.25)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.15
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for name in ("Heading 1", "Heading 2"):
    st = doc.styles[name]
    set_style_font(st, bold=True)
    st.paragraph_format.first_line_indent = Cm(1.25)
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(6)
    st.font.italic = False
for name in ("Caption", "Table Grid"):
    try:
        set_style_font(doc.styles[name])
    except KeyError:
        pass


def p(text, style=None, align=None, indent=True):
    par = doc.add_paragraph(text, style=style)
    if align is not None:
        par.alignment = align
    if not indent:
        par.paragraph_format.first_line_indent = Cm(0)
    return par


def picture(path, width_cm, caption):
    par = p("", align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    par.add_run().add_picture(str(path), width=Cm(width_cm))
    p(caption, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)


def bullets(items, mark="–"):
    for it in items:
        par = p(f"{mark} {it}")
        par.paragraph_format.first_line_indent = Cm(0)
        par.paragraph_format.left_indent = Cm(1.25)


f11, f12, f13 = IMG / "fig1_1.png", IMG / "fig1_2.png", IMG / "fig1_3.png"
figure_1_1(f11); figure_1_2(f12); figure_1_3(f13)

# ---------- Текст из «К заданию 1» ----------
doc.add_heading("Тема 1. Структура КПС «Пегас»", level=1)
p("Комплекс программных средств для информационно-технологической поддержки дистанционного "
  "обучения «Пегас» [1] условно разделен на две большие части (см. рис. 1.1):")
bullets(["сетевую систему дистанционного обучения;", "набор программных средств, работающих в локальном режиме."])
picture(f11, 15, "Рис. 1.1. Схема КПС «Пегас»")
p("Сетевая версия системы базируется на всемирно известной системе поддержки интернет-обучения (LMS) "
  "Moodle [2]. Данная система представляет собой пакет программных средств для создания курсов "
  "дистанционного обучения и web-сайтов. Система распространяется бесплатно как Open Source-проект по "
  "лицензии GNU GPL и может работать на любом сервере. Система переведена на 70 языков и используется "
  "в 134 странах мира. С помощью данной системы можно организовать обучение до 40000 студентов. Система "
  "спроектирована с учётом достижений современной педагогики, акцентируясь на взаимодействии между "
  "студентами и преподавателями. Может использоваться как для дистанционного, так и для очного обучения. "
  "Имеет простой и эффективный интерфейс. Дизайн имеет модульную структуру и легко модифицируется.")
p("С сетевой версией системы «Пегас» можно ознакомиться по адресу pegas.bsu.edu.ru. Процедура установки "
  "сетевой версии, а также вопросы администрирования системы будут подробно рассмотрены в данном учебном пособии.")
p("Сотрудниками ЦДО БелГУ разработаны новые модули и функции, расширяющие возможности LMS Moodle, а также "
  "постоянно выполняется корректировка ядра системы в соответствии с потребностями дистанционного обучения "
  "в БелГУ. Кратко рассмотрим разработанные блоки и программные средства.")
p("Блок «Деканат» позволяет администраторам и методистам ЦДО работать с информацией о факультетах и "
  "специальностях, формировать группы студентов, заполнять личные и учебные карточки студентов, "
  "формировать рабочие учебные планы и т.д.")
p("Блок «Сервис ЦДО» разработан с целью аккумулирования в одном месте всех сервисных функций, "
  "разрабатываемых сотрудниками ЦДО как для администраторов системы, так для пользователей.")
p("Набор локальных программных средств, разработанных сотрудниками Центра дистанционного обучения, "
  "включает в себя следующие программы:")
bullets(["«Пегас Конвертор»;", "«Пегас Генератор»;", "«Пегас Контент Плейер»."], mark="−")
p("Программа «Пегас Конвертор» предназначена для обработки учебно-методических комплексов (УМК), "
  "подготовленных в Microsoft Word. К её основным особенностям можно отнести следующие выполняемые "
  "функции: возможность очистки HTML-кода от лишних тэгов, создаваемых MS Word; разбиение документа на "
  "страницы в соответствии со структурой, определяемой стилями «Заголовок 1», «Заголовок 2» … "
  "«Заголовок 6»; организация просмотра полученных страниц в соответствии с содержанием; создание "
  "архивного файла в формате ZIP; генерацию описания страниц и структуры УМК в формате Moodle XML; "
  "генерацию описания глоссария в формате XML.")
p("Программа «Пегас Генератор» предназначена для генерации архивных файлов, содержащих материалы УМК. "
  "Описание УМК может быть представлено в двух форматах: Moodle XML и в соответствии со спецификацией "
  "IMS. Материалы УМК, содержащие описание в формате Moodle XML, шифруются, помещаются в базу данных "
  "формата MDB и упаковываются в формате ZIP. Полученные архивные файлы предназначены для использования "
  "программой «Пегас Контент Плейер». Материалы УМК, описание которых сгенерировано в соответствии со "
  "спецификацией IMS могут быть импортированы в среду Виртуального Университета (www.openet.ru) или "
  "использоваться в системе МЕТА.")
p("Программа «Пегас Контент Плейер» предназначена для воспроизведения учебно-методических материалов "
  "курсов, записанных в формате системы дистанционного обучения «Пегас». К основным функциям программы "
  "относятся: отображение списка курсов по изучаемой специальности с указанием названия курса, "
  "преподавателей и краткого описания курса; формирование иерархической структуры курса, определенного "
  "в XML-формате; воспроизведение тестовых вопросов в случайном порядке и выдача статистики прохождения теста.")

doc.add_heading("1.1 Технические требования при развертывании среды в образовательном учреждении", level=2)
p("Рассмотрим сначала требования, предъявляемые к программному обеспечению сервера, на котором будет "
  "развернута система дистанционного обучения «Пегас Портал» на базе Moodle.")
p("Система Moodle изначально разрабатывалась для операционной системы (ОС) Linux, использующей "
  "веб-сервер Apache, систему управления базами данных MySQL и интерпретатор языка программирования PHP. "
  "Данный набор программного обеспечения известен под названием LAMP-платформы. В качестве операционной "
  "системы может выступать также и одна из ОС семейства Windows (XP/2000/2003).")
p("При выборе установочных пакетов Apache, MySQL и PHP не стоит загружать их последние версии. Лучше "
  "скачать более ранние, но и более надежные дистрибутивы.")
p("В качестве веб-сервера лучше всего использовать Apache HTTP Server версии 2.0.x, где x может меняться "
  "от 54 и выше. В настоящем пособии рассматривается версия дистрибутива Apache 2.0.54 (файл - "
  "apache_2.0.54-win32-x86-no_ssl.msi). Загрузить дистрибутив Apache можно со страницы "
  "http://httpd.apache.org/download.cgi.")
p("С PHP также возникает проблема выбора дистрибутива, как и с Apache. Сейчас доступны две версии: "
  "PHP 5.2.2 и PHP 4.4.7. Однако их использовать не рекомендуется по той причине, что LMS Moodle версии "
  "1.4.x и 1.5.x разрабатывалась с учетом возможностей PHP 4.1.0, а версия Moodle 1.6 ориентирована на "
  "использование PHP 4.3.0. Поэтому лучше всего скачать один из дистрибутивов PHP 4.3.x. Сделать это "
  "можно со страницы http://ru.php.net/releases/index.php. Обратите внимание, что инсталлятор в виде "
  "exe-файла - это сильно урезанная версия PHP. Кроме нее Вам нужно скачать zip-архив с полной версией, "
  "которая содержит расширения PHP. В настоящем пособии рассматривается версия дистрибутива PHP 4.3.11 "
  "(файлы php-4.3.11-installer.exe и php-4.3.11-Win32.zip).")
p("В качестве системы управления базами данных лучше всего использовать MySQL 4.1. В настоящем пособии "
  "рассматривается версия дистрибутива MySQL 4.1.16 (файл - mysql-4.1.16-win32.zip). Загрузить данный "
  "файл можно со страницы http://www.mysql.ru/download/.")
p("Требования, предъявляемые к аппаратному обеспечению, следующие:")
p("– дисковое пространство: минимум 220 Мб, максимум зависит от количества курсов и их объема;")
p("– оперативная память: минимум 256 Mб, рекомендуется 1 Гб. Общее правило определения объема ОП "
  "задается следующим образом: Moodle может поддерживать работу 50 параллельных пользователей при "
  "наличии 1 Гб оперативной памяти, т.е. для того чтобы обеспечить нормальную одновременную работу 25 "
  "пользователей в режиме онлайн необходимо 512 Мб памяти. Количество пользователей, зарегистрированных "
  "в системе, не зависит от объема ОП (например, на момент написания пособия на сайте Moodle.org было "
  "зарегистрировано более 200 000 пользователей).")

doc.add_heading("1.2 Установка, настройка и конфигурирование сервера", level=2)
p("Прежде чем приступать к установке и настройке серверного программного обеспечения необходимо "
  "определиться со структурой папок сервера. Наиболее оптимальной является структура, построенная по "
  "следующим принципам:")
p("– все приложения сервера сосредоточены в одной папке (как правило, это usr);")
p("– приложения AMP-платформы устанавливаются в папку local;")
p("– исходный код систем Moodle, phpMyAdmin, сайты и т.п. записываются в папку wwwroot.")
p("Таким образом, мы получаем чёткую структуризацию серверного ПО и, при необходимости организации "
  "удаленного доступа к компонентам сервера, достаточно открыть доступ к одной папке usr. Примерная "
  "структура папок показана на рис. 1.2.")
picture(f12, 5.5, "Рис. 1.2. Примерная структура папок сервера.")
p("Перед началом установки дистрибутивов создайте на диске С: папки usr, local и wwwroot. Остальные "
  "папки будут создаваться по мере установки компонент сервера.")

doc.add_heading("1.3 Установка и настройка сервера Apache 2.0 под Windows XP", level=2)
p("1. Для запуска процесса установки дважды щелкните на файле дистрибутива "
  "apache_2.0.54-win32-x86-no_ssl.msi. Появится первое окно мастера установки (рис. 1.3):")
picture(f13, 12, "Рис. 1.3. Окно с приветствием мастера установки Apache")

# ---------- 1.5 Таблица ----------
p("Таблица 1. Ассортимент фруктов в магазине", align=WD_ALIGN_PARAGRAPH.RIGHT, indent=False).paragraph_format.space_before = Pt(12)
fruits = [("№", "Наименование", "Страна-производитель", "Цена за 1 кг, руб.", "Остаток на складе, кг"),
          ("1", "Яблоки «Гала»", "Россия", "149", "120"),
          ("2", "Бананы", "Эквадор", "129", "85"),
          ("3", "Апельсины", "Египет", "159", "64"),
          ("4", "Груши «Конференция»", "Бельгия", "239", "40"),
          ("5", "Виноград «Кишмиш»", "Узбекистан", "289", "32"),
          ("6", "Мандарины", "Турция", "199", "70")]
t = doc.add_table(rows=len(fruits), cols=len(fruits[0]))
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for r, row in enumerate(fruits):
    for c, val in enumerate(row):
        cell = t.cell(r, c)
        cell.text = val
        par = cell.paragraphs[0]
        par.paragraph_format.first_line_indent = Cm(0)
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT if c == 1 and r else WD_ALIGN_PARAGRAPH.CENTER
        if r == 0:
            par.runs[0].bold = True

# ---------- 1.2 Оглавление в конце документа ----------
doc.add_page_break()
p("Оглавление", align=WD_ALIGN_PARAGRAPH.CENTER, indent=False).runs[0].bold = True
add_field(p("", indent=False), 'TOC \\o "1-3" \\h \\z \\u', "Обновите поле (F9), чтобы построить оглавление")

# ---------- 1.4 Нумерация страниц ----------
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.paragraph_format.first_line_indent = Cm(0)
add_field(fp, "PAGE", "1")

# ---------- 1.3 Весь текст 11 пт ----------
for par in doc.paragraphs + [c.paragraphs[0] for row in t.rows for c in row.cells] + [fp]:
    for run in par.runs:
        run.font.size = SIZE
        run.font.name = FONT

doc.save(OUT)
print("saved", OUT)
