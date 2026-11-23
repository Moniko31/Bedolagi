/* ==========================================================================
   main.js — вся интерактивность сайта, без библиотек.
   ========================================================================== */
(function () {
  'use strict';

  // Класс .js ставится inline-скриптом в <head>: без JS контент виден сразу.

  const $ = (s, ctx = document) => ctx.querySelector(s);
  const $$ = (s, ctx = document) => Array.from(ctx.querySelectorAll(s));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. Тема (светлая / тёмная) ---------- */
  const themeToggle = $('#themeToggle');
  themeToggle.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* приватный режим: просто не запоминаем */ }
  });

  /* ---------- 2. Шапка при скролле + кнопка «наверх» ---------- */
  const header = $('#header');
  const toTop = $('#toTop');
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 10);
    toTop.classList.toggle('is-visible', y > 700);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }));

  /* ---------- 3. Мобильное меню (бургер) ---------- */
  const burger = $('#burger');
  const nav = $('#nav');
  const setMenu = (open) => {
    nav.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    document.body.classList.toggle('no-scroll', open);
  };
  burger.addEventListener('click', () => setMenu(!nav.classList.contains('is-open')));
  // Закрываем меню по клику на ссылку, по Esc и при переходе на десктоп
  $$('a', nav).forEach((a) => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
  window.matchMedia('(min-width: 1080px)').addEventListener('change', (e) => { if (e.matches) setMenu(false); });

  /* ---------- 4. Плавная прокрутка по якорям ----------
     scroll-behavior: smooth в CSS делает основную работу,
     здесь — обновляем адрес без «прыжка» и учитываем reduced motion. */
  $$('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      const id = link.getAttribute('href');
      if (id.length < 2) return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
      history.replaceState(null, '', id);
    });
  });

  /* ---------- 5. Подсветка активного пункта меню ---------- */
  const navLinks = $$('.nav__link');
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      navLinks.forEach((l) => l.classList.toggle('is-active', l.getAttribute('href') === '#' + entry.target.id));
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  $$('main section[id]').forEach((s) => sectionObserver.observe(s));

  /* ---------- 6. Анимации появления (Intersection Observer) ----------
     Соседние элементы в одном контейнере получают нарастающую задержку. */
  const revealEls = $$('.reveal');
  revealEls.forEach((el) => {
    const siblings = $$(':scope > .reveal', el.parentElement);
    const i = siblings.indexOf(el);
    if (i > 0) el.style.setProperty('--delay', Math.min(i * 0.08, 0.4) + 's');
  });
  const revealObserver = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      // Счётчики в hero запускаются при появлении
      $$('[data-count]', entry.target).forEach(animateCounter);
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  revealEls.forEach((el) => revealObserver.observe(el));

  function animateCounter(el) {
    const end = +el.dataset.count;
    const suffix = el.dataset.suffix || '+';
    if (reduceMotion) { el.textContent = end + suffix; return; }
    const duration = 1600;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(end * eased) + (p === 1 ? suffix : '');
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* ---------- 7. Фильтр портфолио ---------- */
  const filters = $$('.filter');
  const works = $$('.work');
  filters.forEach((btn) => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.filter;
      filters.forEach((b) => {
        const active = b === btn;
        b.classList.toggle('is-active', active);
        b.setAttribute('aria-pressed', String(active));
      });
      works.forEach((w) => {
        const show = cat === 'all' || w.dataset.category === cat;
        w.classList.remove('is-appearing');
        w.classList.toggle('is-hidden', !show);
        if (show) {
          w.classList.add('is-visible'); // на случай, если ещё не «проявился» скроллом
          void w.offsetWidth;            // перезапуск анимации
          w.classList.add('is-appearing');
        }
      });
    });
  });

  /* ---------- 8. Слайдер отзывов: кнопки, точки, свайп, автопрокрутка ---------- */
  const slider = $('#slider');
  if (slider) {
    const track = $('.slider__track', slider);
    const slides = $$('.testimonial', track);
    const dotsWrap = $('.slider__dots', slider);
    let index = 0;
    let timer = null;
    const AUTOPLAY_MS = 6000;

    const dots = slides.map((_, i) => {
      const d = document.createElement('button');
      d.className = 'slider__dot';
      d.setAttribute('role', 'tab');
      d.setAttribute('aria-label', 'Отзыв ' + (i + 1));
      d.addEventListener('click', () => { go(i); restart(); });
      dotsWrap.appendChild(d);
      return d;
    });

    function go(i) {
      index = (i + slides.length) % slides.length;
      track.style.transform = 'translateX(' + (-index * 100) + '%)';
      dots.forEach((d, n) => {
        d.classList.toggle('is-active', n === index);
        d.setAttribute('aria-selected', String(n === index));
      });
      slides.forEach((s, n) => s.setAttribute('aria-hidden', String(n !== index)));
    }
    const restart = () => {
      clearInterval(timer);
      if (!reduceMotion) timer = setInterval(() => go(index + 1), AUTOPLAY_MS);
    };

    $$('.slider__btn', slider).forEach((b) => b.addEventListener('click', () => {
      go(index + (b.dataset.dir === 'next' ? 1 : -1));
      restart();
    }));

    // Пауза при наведении / фокусе
    slider.addEventListener('mouseenter', () => clearInterval(timer));
    slider.addEventListener('mouseleave', restart);
    slider.addEventListener('focusin', () => clearInterval(timer));
    slider.addEventListener('focusout', restart);

    // Свайп на телефонах
    let startX = 0;
    let dx = 0;
    const viewport = $('.slider__viewport', slider);
    viewport.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; dx = 0; clearInterval(timer); }, { passive: true });
    viewport.addEventListener('touchmove', (e) => { dx = e.touches[0].clientX - startX; }, { passive: true });
    viewport.addEventListener('touchend', () => {
      if (Math.abs(dx) > 50) go(index + (dx < 0 ? 1 : -1));
      restart();
    });

    // Стрелки клавиатуры, когда фокус внутри слайдера
    slider.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') { go(index + 1); restart(); }
      if (e.key === 'ArrowLeft') { go(index - 1); restart(); }
    });

    go(0);
    restart();
  }

  /* ---------- 9. FAQ-аккордеон (открыт только один пункт) ---------- */
  const accItems = $$('.acc-item');
  accItems.forEach((item) => {
    const btn = $('.acc-item__btn', item);
    btn.addEventListener('click', () => {
      const willOpen = !item.classList.contains('is-open');
      accItems.forEach((other) => {
        other.classList.remove('is-open');
        $('.acc-item__btn', other).setAttribute('aria-expanded', 'false');
      });
      if (willOpen) {
        item.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  /* ---------- 10. Кнопки тарифов подставляют пакет в форму ---------- */
  $$('[data-plan]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const select = $('#service');
      const opt = Array.from(select.options).find((o) => o.text.includes(btn.dataset.plan));
      if (opt) select.value = opt.value || opt.text;
    });
  });

  /* ---------- 11. Валидация и отправка формы ---------- */
  const form = $('#contactForm');
  const status = $('.form__status', form);
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const PHONE_RE = /^\+?[\d\s\-()]{10,18}$/;

  // Правила проверки для каждого поля: вернуть текст ошибки или ''
  const rules = {
    name: (v) => (v.trim().length < 2 ? 'Укажите имя (минимум 2 символа)' : ''),
    contact: (v) => {
      v = v.trim();
      if (!v) return 'Укажите email или телефон';
      if (!EMAIL_RE.test(v) && !PHONE_RE.test(v)) return 'Похоже, в email или номере ошибка';
      return '';
    },
    message: (v) => (v.trim().length < 10 ? 'Опишите задачу чуть подробнее (от 10 символов)' : ''),
    consent: (_, el) => (!el.checked ? 'Нужно согласие на обработку данных' : ''),
  };

  function validateField(el) {
    const rule = rules[el.name];
    if (!rule) return true;
    const error = rule(el.value, el);
    const field = el.closest('.field');
    field.classList.toggle('has-error', !!error);
    field.classList.toggle('is-valid', !error && el.type !== 'checkbox');
    $('.field__error', field).textContent = error;
    el.setAttribute('aria-invalid', String(!!error));
    return !error;
  }

  // Проверяем поле при уходе с него; после первой ошибки — на лету
  Object.keys(rules).forEach((name) => {
    const el = form.elements[name];
    el.addEventListener('blur', () => validateField(el));
    el.addEventListener('input', () => { if (el.closest('.field').classList.contains('has-error')) validateField(el); });
    el.addEventListener('change', () => validateField(el));
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.className = 'form__status';
    status.textContent = '';

    if (form.elements.website.value) return; // бот заполнил поле-ловушку

    const fields = Object.keys(rules).map((n) => form.elements[n]);
    const results = fields.map(validateField);
    const firstInvalid = fields[results.indexOf(false)];
    if (firstInvalid) { firstInvalid.focus(); return; }

    const btn = $('button[type="submit"]', form);
    const btnText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Отправляем…';

    try {
      await sendForm(Object.fromEntries(new FormData(form)));
      status.classList.add('is-success');
      status.textContent = 'Спасибо! Заявка отправлена, отвечу в течение 2 часов.';
      form.reset();
      $$('.field', form).forEach((f) => f.classList.remove('is-valid'));
    } catch (err) {
      status.classList.add('is-error');
      status.textContent = 'Не удалось отправить. Напишите мне в Telegram или WhatsApp, кнопки справа внизу.';
    } finally {
      btn.disabled = false;
      btn.textContent = btnText;
    }
  });

  /**
   * Отправка заявки. ЗАМЕНИТЕ на свой способ:
   *
   * Вариант A — Formspree (бесплатно, без сервера):
   *   const r = await fetch('https://formspree.io/f/ВАШ_ID', {
   *     method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
   *     body: JSON.stringify(data) });
   *   if (!r.ok) throw new Error('send failed');
   *
   * Вариант B — свой PHP/Node-обработчик:
   *   const r = await fetch('/send.php', { method: 'POST', body: new URLSearchParams(data) });
   *   if (!r.ok) throw new Error('send failed');
   *
   * Не вставляйте токен Telegram-бота прямо в этот файл: его увидит любой посетитель.
   * Для Telegram используйте серверный обработчик (вариант B).
   */
  async function sendForm(data) {
    console.info('Заявка (демо, никуда не отправлена):', data);
    await new Promise((r) => setTimeout(r, 900)); // имитация запроса
  }

  /* ---------- 12. Текущий год в подвале ---------- */
  const year = $('#year');
  if (year) year.textContent = new Date().getFullYear();
})();
