# Сайт фрилансера

## Запуск
Откройте `index.html` в браузере. Для локального сервера:
`python3 -m http.server 8080` → http://localhost:8080

## Что заменить перед публикацией
1. Имя «Иван Петров», «ИП» в логотипе: поиск по `index.html` и `privacy.html`.
2. Контакты: `hello@example.com`, `+79000000000`, `t.me/username`, `wa.me/79000000000`, `vk.com/username`, `behance.net/username`.
3. SEO: `<title>`, `description`, `canonical`, `og:*`, блок JSON-LD (`example.com` → ваш домен).
4. Фото: `.photo-placeholder` → `<img src="img/me.jpg" alt="...">`; работы: `.work__cover` → `<img class="work__img" ...>`.
5. Отзывы, цены, цифры в hero (`data-count`).
6. Отправка формы: функция `sendForm` в `js/main.js` (Formspree или свой обработчик).
7. Цвета: `--primary` и `--accent` в начале `css/style.css`.

## Новая работа в портфолио
Скопируйте `<article class="work reveal" data-category="web">…</article>`.
Категории: `web`, `design`, `copy`, `marketing`. Новая категория: добавьте кнопку `.filter` с таким же `data-filter`.
