# Как подключиться к репозиторию Bedolagi и работать

Репозиторий: https://github.com/Moniko31/Bedolagi (ветка `main`).

Важно: репозиторий публичный. Не коммитьте пароли, токены, ключи, `.env` и данные клиентов.

## Часть 1. Скачать репозиторий на свой компьютер

### 1. Установите Git
- Windows: https://git-scm.com/download/win
- macOS: `brew install git`
- Linux: `sudo apt install git`

Один раз задайте имя и почту:
```
git config --global user.name "Ваше Имя"
git config --global user.email "you@example.com"
```

### 2. Клонируйте репозиторий
Только чтение, без настройки доступа:
```
git clone https://github.com/Moniko31/Bedolagi.git
cd Bedolagi
```

### 3. Настройте доступ на запись (push)
Нужно, чтобы владелец репозитория добавил вас в Settings → Collaborators. Затем выберите один способ.

**Способ А. HTTPS и токен**
1. GitHub → Settings → Developer settings → Personal access tokens → создайте токен с правом `repo`.
2. При `git push` введите логин GitHub, а вместо пароля вставьте токен.

**Способ Б. SSH-ключ**
1. Создайте ключ: `ssh-keygen -t ed25519 -C "you@example.com"`.
2. Скопируйте содержимое `~/.ssh/id_ed25519.pub` в GitHub → Settings → SSH and GPG keys.
3. Клонируйте по SSH: `git clone git@github.com:Moniko31/Bedolagi.git`.

## Часть 2. Ежедневная работа

```
git pull                      # забрать свежие изменения
# ... работаете в work/ или study/ ...
git status                    # что изменилось
git add work/ study/          # добавить нужное (не git add -A вслепую)
git commit -m "Что сделал"
git push
```
Если `git push` отказывает с ошибкой, сделайте `git pull --rebase` и повторите push.

Куда класть файлы:
- Работа → `work/projects`, `work/design`, `work/docs`, `work/assets`.
- Учёба → `study/courses`, `study/notes`, `study/practice`, `study/materials`.

## Часть 3. Работа на сервере через VS Code (Remote-SSH)

1. Установите расширение **Remote - SSH**.
2. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host** → `user@адрес-сервера`.
3. Откройте папку с проектом на сервере (`/root/projects/Bedolagi`).
4. На сервере репозиторий уже подключён: удалённый адрес `ssh` использует ключ доступа сервера. Отправка: `git push ssh main`.

## Часть 4. Penpot (макеты)

Penpot запущен на сервере и слушает порт 9001. Папка с конфигурацией: `penpot/`.

1. Подключитесь к серверу через VS Code Remote-SSH.
2. Вкладка **Ports** → **Forward a Port** → `9001`, затем `4402`.
3. Откройте http://localhost:9001 и войдите. Пароль хранится на сервере и в репозиторий не добавляется.
4. Для работы с Claude Code: порт 4401 (MCP) доступен только на сервере, порт 4402 нужен плагину MCP в браузере. Откройте файл, запустите плагин MCP, затем попросите Claude нарисовать или поправить макет.

Запуск и остановка (на сервере, в папке `penpot/`):
```
docker compose up -d
docker compose down
```

## Если что-то не работает

| Проблема | Что делать |
|---|---|
| `Permission denied (publickey)` | Ключ не добавлен в GitHub или нет прав на репозиторий |
| `403` при push по HTTPS | Токен без права `repo` или вас нет в Collaborators |
| `localhost:9001` не открывается | Не проброшен порт 9001 во вкладке Ports |
| Конфликт при `git pull` | Откройте файлы с маркерами `<<<<<<<`, оставьте нужное, затем `git add` и `git commit` |
