# TTP Bot

Telegram бот для управления заявками.

## Установка и запуск (Локально)

1. Клонируйте репозиторий.
2. Создайте файл `.env` на основе примера (см. ниже).
3. Запустите через Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

## Настройка Деплоя (GitHub Actions)

Чтобы разворачивать бота на сервере по кнопке из GitHub:

1. **Подготовка сервера:**
   * Зайдите на свой VPS/сервер.
   * Установите `docker` и `docker-compose`.
   * Склонируйте этот репозиторий в папку (например, `/root/ttp_bot`):
     ```bash
     git clone https://github.com/Gendalf2475/ttp_bot.git /root/ttp_bot
     ```

2. **Настройка GitHub Secrets:**
   В репозитории на GitHub перейдите в `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`. Добавьте следующие секреты:

   * `SERVER_HOST`: IP-адрес вашего сервера.
   * `SERVER_USER`: Имя пользователя (обычно `root`).
   * `SSH_PRIVATE_KEY`: Ваш приватный SSH ключ (содержимое файла `id_rsa`, без пароля). Публичный ключ должен быть добавлен в `~/.ssh/authorized_keys` на сервере.
   * `ENV_FILE`: Полное содержимое вашего файла `.env`. Скопируйте всё из локального `.env` и вставьте сюда.

3. **Запуск деплоя:**
   * Перейдите во вкладку **Actions** в репозитории.
   * Выберите workflow **Deploy to Server**.
   * Нажмите кнопку **Run workflow**.

## Переменные окружения (.env)

```env
BOT_TOKEN=ваш_токен
GROUP_CHAT_ID=-100...
TOPIC_NEW_ID=...
TOPIC_IN_WORK_ID=...
TOPIC_DECLINED_ID=...
TOPIC_AWAIT_REVIEW_ID=...
TOPIC_APPROVED_ID=...
SUPER_ADMINS=12345,67890
RESPONSIBLE_USERNAMES=@user1,@user2
MYSQL_DATABASE=bot_db
MYSQL_USER=bot_user
MYSQL_PASSWORD=bot_password
MYSQL_ROOT_PASSWORD=root_password
MYSQL_HOST=db
MYSQL_PORT=3306
```
