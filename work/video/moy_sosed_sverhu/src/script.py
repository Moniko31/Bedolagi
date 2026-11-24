"""«Мой сосед сверху» — 1 серия. Сценарий: реплики по кадрам.
who: M — Макс (мужской голос), F — Вера (женский голос).
r — темп %, p — высота Гц, v — громкость %, pre — пауза перед репликой (с), mood — эмоция говорящего.
"""
VOICE = {"M": "en-US-AndrewMultilingualNeural", "F": "en-US-AvaMultilingualNeural"}

LINES = [
    # кадр 1: ночь, кровать сверху, с потолка грохочет музыка
    dict(shot="bed", who="M", t="Три часа ночи...", r=-12, p=-6, v=-15, pre=2.2, mood="sleepy"),
    dict(shot="bed", who="M", t="Да сколько можно?!", r=0, p=4, v=10, pre=0.5, mood="angry"),
    # кадр 2: дверь соседки, стук, дверь открывается — дым
    dict(shot="door", who="F", t="Если вы насчёт музыки — я выключу!", r=8, p=6, v=5, pre=2.4, mood="panic"),
    dict(shot="door", who="F", t="А если насчёт дыма — я не виновата.", r=4, p=0, v=0, pre=0.25, mood="guilty"),
    dict(shot="door", who="M", t="А что ты там жжёшь?", r=-4, p=0, v=0, pre=0.35, mood="suspicious"),
    dict(shot="door", who="F", t="Торт. Маме. У неё юбилей в девять утра.", r=0, p=-4, v=-5, pre=0.3, mood="sad"),
    # кадр 3: крупно сгоревший торт
    dict(shot="cake", who="M", t="Это не торт. Это уголь.", r=-8, p=-4, v=0, pre=0.7, mood="deadpan"),
    # кадр 4: Вера обиделась, закрывает дверь
    dict(shot="vera", who="F", t="Спасибо. Очень поддержал.", r=-6, p=-8, v=-5, pre=0.4, mood="offended"),
    # кадр 5: Макс останавливает дверь
    dict(shot="stop", who="M", t="Стой. Мука есть? Яйца?", r=-2, p=2, v=5, pre=0.5, mood="determined"),
    dict(shot="stop", who="F", t="Есть... А что?", r=-6, p=4, v=-5, pre=0.3, mood="surprised"),
    dict(shot="stop", who="M", t="Тогда открывай. Будем печь заново.", r=-2, p=0, v=0, pre=0.3, mood="smirk"),
    # кадр 6: кухня, оба в муке
    dict(shot="kitchen", who="F", t="Подожди, ты что, умеешь печь?", r=4, p=8, v=0, pre=1.0, mood="surprised"),
    dict(shot="kitchen", who="M", t="Бабушка научила. Только никому.", r=-4, p=-2, v=-5, pre=0.3, mood="smirk"),
    dict(shot="kitchen", who="F", t="Могила.", r=0, p=6, v=0, pre=0.25, mood="happy"),
    # кадр 7: 05:40, духовка дзынь, идеальный торт
    dict(shot="oven", who="F", t="Слушай... а как тебя зовут-то?", r=-4, p=2, v=-5, pre=1.6, mood="happy"),
    dict(shot="oven", who="M", t="Макс. С пятого этажа.", r=-2, p=0, v=0, pre=0.3, mood="smirk"),
    dict(shot="oven", who="F", t="Вера. Та самая, с музыкой.", r=0, p=4, v=0, pre=0.3, mood="happy"),
    # кадр 8: следующий вечер, Вера у двери Макса
    dict(shot="final", who="F", t="Мама сказала, это лучший торт в её жизни.", r=2, p=4, v=0, pre=1.2, mood="happy"),
    dict(shot="final", who="M", t="Тогда с тебя ужин.", r=-4, p=-2, v=0, pre=0.35, mood="smirk"),
    dict(shot="final", who="F", t="Договорились, сосед. Но музыку выбираю я.", r=0, p=4, v=0, pre=0.35, mood="happy"),
]
TAIL = 3.2   # финальная заставка после последней реплики

for L in LINES:
    L.setdefault("sub", "- " + L["t"])
