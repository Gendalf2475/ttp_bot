import telebot
from telebot import types
import sqlite3
from datetime import datetime, date

# ================== НАСТРОЙКИ ==================

TOKEN = "8388410449:AAGYkTcHeIYO2HlAn4__al3-HyitUWJbgDo"  # <-- ВСТАВЬ СВОЙ ТОКЕН

GROUP_CHAT_ID = -1003296938318  # твой chat_id

TOPIC_NEW_ID = 19
TOPIC_IN_WORK_ID = 93
TOPIC_DECLINED_ID = 91
TOPIC_AWAIT_REVIEW_ID = 196
TOPIC_APPROVED_ID = 89

SUPER_ADMINS = [528329970]
RESPONSIBLE_USERNAMES = ["@ivanmofa", "@samoylovichivan"]

DB_PATH = "bot.db"

bot = telebot.TeleBot(TOKEN)

# ================== БАЗА ДАННЫХ ==================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'none',
            pending_report_app_id INTEGER,
            pending_report_step INTEGER,
            report_q1 TEXT,
            report_q2 TEXT,
            report_q3 TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            status TEXT,
            moderator_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            taken_at TEXT,
            chat_id INTEGER,
            topic_id INTEGER,
            message_id INTEGER,
            report_q1 TEXT,
            report_q2 TEXT,
            report_q3 TEXT
        )
    """)

    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)


# ================== УТИЛИТЫ ПО ПОЛЬЗОВАТЕЛЮ ==================

def get_or_create_user(user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, username, role,
               pending_report_app_id, pending_report_step,
               report_q1, report_q2, report_q3
        FROM users WHERE user_id = ?
        """,
        (user.id,)
    )
    row = cur.fetchone()
    if row is None:
        role = "none"
        if user.id in SUPER_ADMINS:
            role = "admin"
        cur.execute(
            """
            INSERT INTO users (user_id, username, role,
                               pending_report_app_id, pending_report_step,
                               report_q1, report_q2, report_q3)
            VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL)
            """,
            (user.id, user.username or "", role),
        )
        conn.commit()
        conn.close()
        return {
            "user_id": user.id,
            "username": user.username,
            "role": role,
            "pending_report_app_id": None,
            "pending_report_step": None,
            "report_q1": None,
            "report_q2": None,
            "report_q3": None,
        }

    conn.close()
    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "pending_report_app_id": row[3],
        "pending_report_step": row[4],
        "report_q1": row[5],
        "report_q2": row[6],
        "report_q3": row[7],
    }


def set_role(user_id, role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
    conn.commit()
    conn.close()


def set_pending_report(user_id, app_id_or_none):
    """
    Если app_id_or_none = None -> сбрасываем состояние отчёта
    Если нет -> ставим шаг = 1 и очищаем ответы
    """
    conn = get_conn()
    cur = conn.cursor()
    if app_id_or_none is None:
        cur.execute(
            """
            UPDATE users
            SET pending_report_app_id = NULL,
                pending_report_step = NULL,
                report_q1 = NULL,
                report_q2 = NULL,
                report_q3 = NULL
            WHERE user_id = ?
            """,
            (user_id,),
        )
    else:
        cur.execute(
            """
            UPDATE users
            SET pending_report_app_id = ?,
                pending_report_step = 1,
                report_q1 = NULL,
                report_q2 = NULL,
                report_q3 = NULL
            WHERE user_id = ?
            """,
            (app_id_or_none, user_id),
        )
    conn.commit()
    conn.close()


def update_user_report_step_and_answer(user_id, step, answer_text):
    """
    Сохраняем ответ на текущий шаг и двигаем шаг вперёд
    step = 1,2,3
    """
    conn = get_conn()
    cur = conn.cursor()

    if step == 1:
        cur.execute(
            """
            UPDATE users
            SET report_q1 = ?, pending_report_step = 2
            WHERE user_id = ?
            """,
            (answer_text, user_id),
        )
    elif step == 2:
        cur.execute(
            """
            UPDATE users
            SET report_q2 = ?, pending_report_step = 3
            WHERE user_id = ?
            """,
            (answer_text, user_id),
        )
    elif step == 3:
        cur.execute(
            """
            UPDATE users
            SET report_q3 = ?, pending_report_step = 4
            WHERE user_id = ?
            """,
            (answer_text, user_id),
        )

    conn.commit()
    conn.close()


def get_user_full(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, username, role,
               pending_report_app_id, pending_report_step,
               report_q1, report_q2, report_q3
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "pending_report_app_id": row[3],
        "pending_report_step": row[4],
        "report_q1": row[5],
        "report_q2": row[6],
        "report_q3": row[7],
    }


def get_user_role(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        if user_id in SUPER_ADMINS:
            return "admin"
        return "none"
    return row[0]


# ================== УТИЛИТЫ ПО ЗАЯВКАМ ==================

def create_application_from_message(message):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO applications (
            text, status, moderator_id,
            created_at, updated_at, taken_at,
            chat_id, topic_id, message_id,
            report_q1, report_q2, report_q3
        )
        VALUES (?, 'new', NULL, ?, ?, NULL, ?, ?, ?, NULL, NULL, NULL)
        """,
        (message.text or "", now, now, message.chat.id, message.message_thread_id, message.message_id),
    )
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id


def update_application(app_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cur = conn.cursor()
    set_clause = []
    params = []
    for k, v in fields.items():
        set_clause.append(f"{k} = ?")
        params.append(v)
    set_clause.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(app_id)
    sql = f"UPDATE applications SET {', '.join(set_clause)} WHERE id = ?"
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def get_application(app_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id, text, status, moderator_id,
            created_at, updated_at, taken_at,
            chat_id, topic_id, message_id,
            report_q1, report_q2, report_q3
        FROM applications WHERE id = ?
        """,
        (app_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    keys = [
        "id", "text", "status", "moderator_id",
        "created_at", "updated_at", "taken_at",
        "chat_id", "topic_id", "message_id",
        "report_q1", "report_q2", "report_q3",
    ]
    return dict(zip(keys, row))


# ================== INLINE-КЛАВИАТУРЫ ==================

def get_new_app_keyboard(app_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ В работу", callback_data=f"take:{app_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_pre:{app_id}")
    )
    return kb


def get_in_work_keyboard(app_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📤 Отправить отчёт", callback_data=f"report:{app_id}"))
    return kb


def get_review_keyboard(app_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve:{app_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_final:{app_id}")
    )
    return kb


# ================== КОМАНДЫ ==================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    get_or_create_user(message.from_user)
    bot.reply_to(
        message,
        "Привет! Я бот заявок.\n"
        "Работаю в группе, куда приходят новые заявки.\n"
        "Если у тебя есть роль модератора или администратора, тебе выдадут доступ."
    )


@bot.message_handler(commands=["debug"])
def cmd_debug(message):
    bot.reply_to(
        message,
        f"chat_id: {message.chat.id}\n"
        f"thread_id (topic_id): {message.message_thread_id}"
    )


def is_super_admin(user_id):
    return user_id in SUPER_ADMINS


@bot.message_handler(commands=["addmod", "delmod", "addadmin", "deladmin"])
def cmd_roles(message):
    if not is_super_admin(message.from_user.id):
        bot.reply_to(message, "У тебя нет прав для управления ролями.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Нужно указать user_id.\nПример: /addmod 123456789")
        return

    target = parts[1]

    try:
        target_id = int(target)
    except ValueError:
        bot.reply_to(
            message,
            "В этой версии нужно указывать именно числовой user_id.\n"
            "Его можно узнать через бота @userinfobot."
        )
        return

    cmd = message.text.split()[0].lstrip("/")
    if cmd == "addmod":
        role = "moderator"
    elif cmd == "addadmin":
        role = "admin"
    elif cmd in ("delmod", "deladmin"):
        role = "none"
    else:
        bot.reply_to(message, "Неизвестная команда.")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """
            INSERT INTO users (user_id, username, role,
                               pending_report_app_id, pending_report_step,
                               report_q1, report_q2, report_q3)
            VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL)
            """,
            (target_id, "", role),
        )
    else:
        cur.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, target_id))
    conn.commit()
    conn.close()

    bot.reply_to(message, f"Роль пользователя {target_id} установлена: {role}")


@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    role = get_user_role(message.from_user.id)
    if role != "admin":
        bot.reply_to(message, "Команда доступна только администраторам.")
        return

    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_start_iso = month_start.isoformat()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM applications WHERE created_at >= ?", (month_start_iso,))
    new_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'approved' AND updated_at >= ?",
        (month_start_iso,),
    )
    approved_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE (status = 'declined_pre' OR status = 'declined_final')
          AND updated_at >= ?
        """,
        (month_start_iso,),
    )
    declined_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT moderator_id, COUNT(*) FROM applications
        WHERE taken_at IS NOT NULL AND taken_at >= ?
        GROUP BY moderator_id
        ORDER BY COUNT(*) DESC
        """,
        (month_start_iso,),
    )
    rows = cur.fetchall()
    conn.close()

    text = [
        f"📊 Статистика за текущий месяц ({month_start.strftime('%d.%m.%Y')} - сегодня):",
        "",
        f"Новых заявок: {new_count}",
        f"Одобрено: {approved_count}",
        f"Отклонено: {declined_count}",
        "",
        "👤 Заявки по модераторам:",
    ]

    if not rows:
        text.append("нет данных.")
    else:
        for moderator_id, cnt in rows:
            mention = f"[{moderator_id}](tg://user?id={moderator_id})"
            text.append(f"{mention} — {cnt} заявок")

    bot.reply_to(message, "\n".join(text), parse_mode="Markdown")


# ================== ОБРАБОТКА НОВЫХ ЗАЯВОК ==================

@bot.message_handler(func=lambda m: m.chat.id == GROUP_CHAT_ID and m.message_thread_id == TOPIC_NEW_ID)
def handle_new_application(message):
    # Сообщение приходит из Google Script в топик "новые заявки"
    app_id = create_application_from_message(message)
    kb = get_new_app_keyboard(app_id)

    # Отправляем НОВОЕ сообщение с номером заявки и кнопками
    sent = bot.send_message(
        GROUP_CHAT_ID,
        f"Заявка #{app_id}\n\n{message.text}",
        message_thread_id=TOPIC_NEW_ID,
        reply_markup=kb
    )

    # Обновляем в БД привязку к новому сообщению
    update_application(
        app_id,
        chat_id=sent.chat.id,
        topic_id=sent.message_thread_id,
        message_id=sent.message_id,
    )

    # Удаляем оригинальное сообщение без кнопок
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass


# ================== CALLBACK'И ==================
def ensure_application_exists(call):
    """Создаёт заявку в БД, если она ещё не создана."""

    message = call.message
    full_text = message.text or ""

    # Удаляем старую шапку "⚡ НОВАЯ ЗАЯВКА ⚡"
    lines = full_text.split("\n")
    body_lines = [l for l in lines if not ("НОВАЯ ЗАЯВКА" in l)]
    body_text = "\n".join(body_lines).strip()

    conn = get_conn()
    cur = conn.cursor()

    # Ищем заявку по message_id (если она уже создана ранее)
    cur.execute(
        "SELECT id FROM applications WHERE message_id = ?",
        (message.message_id,)
    )
    row = cur.fetchone()

    if row:
        conn.close()
        return row[0], body_text

    # Создаём новую заявку
    cur.execute(
        """
        INSERT INTO applications (
            text, status, moderator_id,
            created_at, updated_at, taken_at,
            chat_id, topic_id, message_id
        )
        VALUES (?, 'new', NULL, ?, ?, NULL, ?, ?, ?)
        """,
        (
            body_text,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            message.chat.id,
            message.message_thread_id,
            message.message_id,
        )
    )
    app_id = cur.lastrowid
    conn.commit()
    conn.close()

    return app_id, body_text
    def auto_format_new_app(message):
    """Автоматически формирует заявку, если пришло сообщение от Google Script."""
    if message.chat.id != GROUP_CHAT_ID:
        return
    if message.message_thread_id != TOPIC_NEW_ID:
        return

    full_text = message.text or ""
    if not full_text.strip():
        return  # игнорируем пустые сообщения

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO applications (
            text, status, moderator_id,
            created_at, updated_at, taken_at,
            chat_id, topic_id, message_id
        ) VALUES (?, 'new', NULL, ?, ?, NULL, ?, ?, ?)
    """, (
        full_text,
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat(),
        message.chat.id,
        message.message_thread_id,
        message.message_id,
    ))

    app_id = cur.lastrowid
    conn.commit()
    conn.close()

    new_text = f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n{full_text}"

    sent = bot.send_message(
        GROUP_CHAT_ID,
        new_text,
        message_thread_id=TOPIC_NEW_ID,
        reply_markup=get_new_app_keyboard(app_id)
    )

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


# handler для обработки сообщений
@bot.message_handler(func=lambda message: True)
def catch(message):
    auto_format_new_app(message)
@bot.callback_query_handler(func=lambda call: True)


def callback_handler(call):
    app_id, body_text = ensure_application_exists(call)
    data = call.data or ""
    user_id = call.from_user.id
    role = get_user_role(user_id)

    def need_moderator():
        bot.answer_callback_query(call.id, "Недостаточно прав.")
        return

    # ============ ВЗЯТЬ В РАБОТУ ============
    if data.startswith("take:"):
        if role not in ("moderator", "admin"):
            return need_moderator()

        app_id, body_text = ensure_application_exists(call)
        app = get_application(app_id)

        new_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"В работе: [{user_id}](tg://user?id={user_id})"
        )

        sent = bot.send_message(
            GROUP_CHAT_ID,
            new_text,
            message_thread_id=TOPIC_IN_WORK_ID,
            reply_markup=get_in_work_keyboard(app_id),
            parse_mode="Markdown"
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        update_application(
            app_id,
            status="in_work",
            moderator_id=user_id,
            taken_at=datetime.utcnow().isoformat(),
            chat_id=sent.chat.id,
            topic_id=sent.message_thread_id,
            message_id=sent.message_id,
        )

        bot.answer_callback_query(call.id, "Заявка взята в работу.")

    # ============ ОТКЛОНИТЬ ДО РАССМОТРЕНИЯ ============
    elif data.startswith("reject_pre:"):
        if role not in ("moderator", "admin"):
            return need_moderator()

        app_id, body_text = ensure_application_exists(call)

        text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"❌ Отклонена до рассмотрения модератором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        bot.send_message(
            GROUP_CHAT_ID,
            text,
            message_thread_id=TOPIC_DECLINED_ID,
            parse_mode="Markdown"
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        update_application(app_id, status="declined_pre")
        bot.answer_callback_query(call.id, "Заявка отклонена.")

    # ============ ОТЧЕТ ============
    elif data.startswith("report:"):
        if role not in ("moderator", "admin"):
            return need_moderator()

        app_id, _ = ensure_application_exists(call)
        app = get_application(app_id)

        set_pending_report(user_id, app_id)
        bot.answer_callback_query(call.id, "Переходим к отчету.")

        bot.send_message(
            user_id,
            f"Отчёт по заявке #{app_id}.\n\n"
            f"Вопрос 1:\nУкажите количество верных ответов"
        )

    # ============ ОДОБРИТЬ ============
    elif data.startswith("approve:"):
        if role != "admin":
            return need_moderator()

        app_id, body_text = ensure_application_exists(call)
        app = get_application(app_id)

        approved_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"✅ Одобрена администратором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        bot.send_message(
            GROUP_CHAT_ID,
            approved_text,
            message_thread_id=TOPIC_APPROVED_ID,
            parse_mode="Markdown"
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        update_application(app_id, status="approved")
        bot.answer_callback_query(call.id, "Заявка одобрена.")

    # ============ ОТКЛОНИТЬ ПОСЛЕ РАССМОТРЕНИЯ ============
    elif data.startswith("reject_final:"):
        if role != "admin":
            return need_moderator()

        app_id, body_text = ensure_application_exists(call)
        app = get_application(app_id)

        declined_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"❌ Отклонена после рассмотрения администратором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        bot.send_message(
            GROUP_CHAT_ID,
            declined_text,
            message_thread_id=TOPIC_DECLINED_ID,
            parse_mode="Markdown"
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        update_application(app_id, status="declined_final")
        bot.answer_callback_query(call.id, "Заявка отклонена окончательно.")

    else:
        bot.answer_callback_query(call.id, "Неизвестное действие.")


# ================== ПРИЁМ ОТЧЁТОВ В ЛИЧКУ ==================

@bot.message_handler(func=lambda m: m.chat.type == "private")
def handle_private(message):
    user_db = get_or_create_user(message.from_user)

    if user_db["role"] not in ("moderator", "admin"):
        bot.reply_to(message, "У тебя нет прав отправлять отчёты.")
        return

    user_state = get_user_full(message.from_user.id)
    app_id = user_state["pending_report_app_id"]
    step = user_state["pending_report_step"]

    if not app_id or not step:
        bot.reply_to(message, "Нет заявки, по которой ожидается отчёт.")
        return

    app = get_application(app_id)
    if not app:
        bot.reply_to(message, "Заявка не найдена.")
        set_pending_report(message.from_user.id, None)
        return

    if step == 1:
        update_user_report_step_and_answer(message.from_user.id, 1, message.text.strip())
        bot.reply_to(
            message,
            "Вопрос 2:\n"
            "Комментарий по прошедшему обзвону"
        )
        return

    if step == 2:
        update_user_report_step_and_answer(message.from_user.id, 2, message.text.strip())
        bot.reply_to(
            message,
            "Вопрос 3:\n"
            "Ссылка на запись обзвона"
        )
        return

    if step == 3:
        update_user_report_step_and_answer(message.from_user.id, 3, message.text.strip())

        user_state = get_user_full(message.from_user.id)
        q1 = user_state["report_q1"] or "-"
        q2 = user_state["report_q2"] or "-"
        q3 = user_state["report_q3"] or "-"

        update_application(
            app_id,
            status="awaiting_review",
            report_q1=q1,
            report_q2=q2,
            report_q3=q3,
        )

        mention_mod = f"[{message.from_user.id}](tg://user?id={message.from_user.id})"
        resp_mentions = " ".join(RESPONSIBLE_USERNAMES) if RESPONSIBLE_USERNAMES else ""
        text = (
            f"{resp_mentions}\n\n"
            f"Заявка #{app_id}\n\n"
            f"{app['text']}\n\n"
            f"Отчёт модератора {mention_mod}:\n\n"
            f"1️⃣ Укажите количество верных ответов:\n{q1}\n\n"
            f"2️⃣ Комментарий по прошедшему обзвону:\n{q2}\n\n"
            f"3️⃣ Ссылка на запись обзвона:\n{q3}"
        )

        sent = bot.send_message(
            GROUP_CHAT_ID,
            text,
            message_thread_id=TOPIC_AWAIT_REVIEW_ID,
            reply_markup=get_review_keyboard(app_id),
            parse_mode="Markdown"
        )

        update_application(
            app_id,
            chat_id=sent.chat.id,
            topic_id=sent.message_thread_id,
            message_id=sent.message_id,
        )

        set_pending_report(message.from_user.id, None)

        bot.reply_to(message, "Отчёт отправлен на рассмотрение.")
        return

    set_pending_report(message.from_user.id, None)
    bot.reply_to(message, "Состояние отчёта сброшено. Попробуй ещё раз через кнопку под заявкой.")


# ================== ЗАПУСК ==================

if __name__ == "__main__":
    init_db()
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    bot.infinity_polling()