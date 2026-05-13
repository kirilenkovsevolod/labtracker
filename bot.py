from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters

TOKEN = "8653168095:AAEsEtIQdDOZHXaSquGjvvxkriRnYn2V0O0"

API_URL = "http://127.0.0.1:8000"

user_states = {}


async def handle_lab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("lab_"):
        lab_id = data.split("_")[1]

        # получаем название лабы с сервера
        lab_info = requests.get(f"{API_URL}/lab/{lab_id}").json()
        lab_title = lab_info.get("title", f"Лабораторная {lab_id}")

        keyboard = [
            [InlineKeyboardButton("Сдать ✅", callback_data=f"submit_{lab_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_labs")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            lab_title,
            reply_markup=reply_markup
        )

    elif data.startswith("submit_"):
        lab_id = data.split("_")[1]
        user_id = query.from_user.id

        requests.post(f"{API_URL}/submit", params={
            "student_id": user_id,
            "lab_id": lab_id
        })

        await query.edit_message_text(f"Лабораторная сдана ✅")

    elif data == "back_to_labs":
        login = context.user_data.get("saved_login", "")

        response = requests.get(f"{API_URL}/labs", params={"login": login})
        labs = response.json()

        statuses = requests.get(f"{API_URL}/status", params={"login": login}).json()
        status_map = {s["lab_id"]: s["status"] for s in statuses}

        keyboard = []
        for lab in labs:
            status = status_map.get(lab["id"], "none")
            if status == "done":
                icon = "✅"
            elif status == "pending":
                icon = "⏳"
            else:
                icon = "❌"

            keyboard.append([
                InlineKeyboardButton(
                    f"{lab['title']} {icon}",
                    callback_data=f"lab_{lab['id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Вот список лабораторных:", reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите логин:")
    user_id = update.message.from_user.id
    user_states[user_id] = "login"


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Поддержка: юзернейм поддержки")


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
        login = context.user_data["login"]
        password = text

        response = requests.post(f"{API_URL}/login", json={
            "login": login,
            "password": password,
            "telegram_id": user_id
        })

        if response.status_code == 200:
            data = response.json()
            context.user_data["saved_login"] = login  # сохраняем логин

            keyboard = [
                ["📚 Лабораторные"],
                ["ℹ️ Помощь"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"Добро пожаловать, {data['name']} из группы {data['group_name']}",
                reply_markup=reply_markup
            )
            user_states[user_id] = None
        else:
            await update.message.reply_text("❌ Неверный логин или пароль")
            await update.message.reply_text("Введите логин:")
            user_states[user_id] = "login"
        return

    if "Лабораторные" in text:
        login = context.user_data.get("saved_login", "")

        response = requests.get(f"{API_URL}/labs", params={"login": login})
        labs = response.json()

        statuses = requests.get(f"{API_URL}/status", params={"login": login}).json()
        status_map = {s["lab_id"]: s["status"] for s in statuses}

        keyboard = []
        for lab in labs:
            status = status_map.get(lab["id"], "none")
            if status == "done":
                icon = "✅"
            elif status == "pending":
                icon = "⏳"
            else:
                icon = "❌"

            keyboard.append([
                InlineKeyboardButton(
                    f"{lab['title']} {icon}",
                    callback_data=f"lab_{lab['id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вот список лабораторных:", reply_markup=reply_markup)

    elif "Помощь" in text:
        await update.message.reply_text("Используй кнопки для навигации")


async def labs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login = context.user_data.get("saved_login", "")
    response = requests.get(f"{API_URL}/labs", params={"login": login})
    labs = response.json()
    text = "\n".join([l["title"] for l in labs])
    await update.message.reply_text(text if text else "Нет лабораторных")


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_lab))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("labs", labs))

app.run_polling()
