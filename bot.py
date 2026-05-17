from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import datetime
from telegram import Update
import re
TOKEN = "8653168095:AAEsEtIQdDOZHXaSquGjvvxkriRnYn2V0O0"
API_URL = "http://127.0.0.1:8000"

user_states = {}

def format_deadline(deadline: str) -> str:
    if not deadline:
        return ""
    try:
        d = datetime.datetime.strptime(deadline, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except Exception:
        return deadline

# ── Напоминания ───────────────────────────────────────────────────────────────

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    for days in [2, 1]:
        try:
            reminders = requests.get(f"{API_URL}/reminders", params={"days_before": days}).json()
            for r in reminders:
                await context.bot.send_message(
                    chat_id=r["telegram_id"],
                    text=(
                        f"⏰ <b>Напоминание!</b>\n\n"
                        f"Лабораторная: <b>{r['lab_title']}</b>\n"
                        f"Дедлайн: <b>{format_deadline(r['deadline'])}</b>\n"
                        f"Осталось: <b>{r['days_before']} {'день' if days == 1 else 'дня'}</b>\n\n"
                        f"Не забудь сдать!"
                    ),
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Ошибка напоминания: {e}")

# ── Список лаб ────────────────────────────────────────────────────────────────

async def show_labs(update=None, query=None, login="", telegram_id=0, edit=False):
    labs = requests.get(f"{API_URL}/labs", params={"login": login, "telegram_id": telegram_id}).json()
    statuses = requests.get(f"{API_URL}/status", params={"login": login, "telegram_id": telegram_id}).json()
    status_map = {s["lab_id"]: s["status"] for s in statuses}

    keyboard = []
    for lab in labs:
        status = status_map.get(lab["id"], "none")
        icon = "✅" if status == "done" else ("⏳" if status == "pending" else "❌")
        deadline = f" | до {format_deadline(lab['deadline'])}" if lab.get("deadline") else ""
        num = re.search(r'№?\s*(\d+)', lab['title'])
        short = f"Лабораторная №{num.group(1)}" if num else lab['title']
        keyboard.append([InlineKeyboardButton(
            f"{short} {icon}{deadline}",
            callback_data=f"lab_{lab['id']}"
        )])

    text = "Вот список лабораторных:" if keyboard else "Лабораторных пока нет."
    markup = InlineKeyboardMarkup(keyboard)

    if edit and query:
        await query.edit_message_text(text, reply_markup=markup)
    elif update:
        await update.message.reply_text(text, reply_markup=markup)

# ── Кнопки ───────────────────────────────────────────────────────────────────

async def handle_lab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    login = context.user_data.get("saved_login", "")

    if data.startswith("lab_"):
        lab_id = int(data.split("_")[1])
        lab = requests.get(f"{API_URL}/lab/{lab_id}").json()

        text = f"<b>{lab['title']}</b>\n\n"
        if lab.get("content"):
            text += f"{lab['content']}\n\n"
        if lab.get("deadline"):
            text += f"📅 Дедлайн: {format_deadline(lab['deadline'])}\n\n"

        keyboard = []
        if lab.get("file_path"):
            keyboard.append([InlineKeyboardButton("📄 Скачать файл лабораторной", callback_data=f"getfile_{lab_id}")])
        keyboard.append([InlineKeyboardButton("Сдать ✅", callback_data=f"try_submit_{lab_id}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_labs")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("try_submit_"):
        lab_id = int(data.split("_")[2])
        lab = requests.get(f"{API_URL}/lab/{lab_id}").json()

        question_id = lab.get("random_question_id")
        question_text = lab.get("random_question", "")

        if not question_id:
            # нет вопросов — сдаём сразу
            requests.post(f"{API_URL}/submit", params={"student_id": user_id, "lab_id": lab_id})
            await query.edit_message_text("Лабораторная сдана ✅")
            return

        context.user_data["pending_lab_id"] = lab_id
        context.user_data["pending_question_id"] = question_id
        user_states[user_id] = "answering"

        await query.edit_message_text(
            f"❓ <b>Контрольный вопрос:</b>\n\n{question_text}\n\nНапишите ответ в чат:",
            parse_mode="HTML"
        )

    elif data.startswith("getfile_"):
        lab_id = int(data.split("_")[1])
        file_url = f"{API_URL}/lab/{lab_id}/file"
        try:
            r = requests.get(file_url, stream=True)
            if r.status_code == 200:
                # получаем имя файла из заголовка
                cd = r.headers.get("content-disposition", "")
                fname = "lab_file"
                if "filename=" in cd:
                    fname = cd.split("filename=")[-1].strip('"')
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(fname)[1]) as tmp:
                    for chunk in r.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(tmp_path, "rb"),
                    filename=fname
                )
                os.unlink(tmp_path)
            else:
                await query.answer("Файл не найден", show_alert=True)
        except Exception as e:
            await query.answer(f"Ошибка: {e}", show_alert=True)

    elif data == "back_to_labs":
        await show_labs(query=query, login=login, telegram_id=user_id, edit=True)

# ── Сообщения ─────────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = user_states.get(user_id)

    if state == "login":
        context.user_data["login"] = text
        user_states[user_id] = "password"
        await update.message.reply_text("Введите пароль:")
        return

    elif state == "password":
        login_val = context.user_data["login"]
        response = requests.post(f"{API_URL}/login", json={
            "login": login_val, "password": text, "telegram_id": user_id
        })
        if response.status_code == 200:
            info = response.json()
            context.user_data["saved_login"] = login_val
            keyboard = [["📚 Лабораторные"], ["ℹ️ Помощь"]]
            await update.message.reply_text(
                f"Добро пожаловать, {info['name']} из группы {info['group_name']}",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            user_states[user_id] = None
        else:
            await update.message.reply_text("❌ Неверный логин или пароль")
            await update.message.reply_text("Введите логин:")
            user_states[user_id] = "login"
        return

    elif state == "answering":
        lab_id = context.user_data.get("pending_lab_id")
        question_id = context.user_data.get("pending_question_id")

        await update.message.reply_text("⏳ Проверяю ответ...")

        try:
            check = requests.post(
                f"{API_URL}/check_answer",
                params={"question_id": question_id, "answer": text}
            ).json()

            if check.get("correct"):
                requests.post(f"{API_URL}/submit", params={"student_id": user_id, "lab_id": lab_id})
                await update.message.reply_text("✅ <b>Верно! Лабораторная сдана.</b>", parse_mode="HTML")
            else:
                await update.message.reply_text(
                    "❌ <b>Неверно.</b>\nПопробуй ещё раз через список лабораторных.",
                    parse_mode="HTML"
                )
        except Exception as e:
            await update.message.reply_text(f"Ошибка проверки: {e}")

        user_states[user_id] = None
        context.user_data.pop("pending_lab_id", None)
        context.user_data.pop("pending_question_id", None)
        return

    if "Лабораторные" in text:
        await show_labs(update=update, login=context.user_data.get("saved_login", ""), telegram_id=user_id)
    elif "Помощь" in text:
        await update.message.reply_text("Используй кнопки для навигации")

# ── Команды ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите логин:")
    user_states[update.message.from_user.id] = "login"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Поддержка: юзернейм поддержки")

# ── Запуск ────────────────────────────────────────────────────────────────────

app = ApplicationBuilder().token(TOKEN).build()

app.job_queue.run_daily(
    send_reminders,
    time=datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc)
)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_lab))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))

app.run_polling()
