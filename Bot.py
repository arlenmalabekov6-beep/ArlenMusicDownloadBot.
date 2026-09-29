import os
import threading

from flask import Flask
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

app_web = Flask(__name__)


@app_web.route("/")
def home():
    return "Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🎵\n\n"
        "Отправь мне ссылку на Instagram."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "instagram.com" in text:
        await update.message.reply_text(
            "Ссылку получил! 🔗\n"
            "Обработка пока находится в разработке."
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, отправь ссылку на Instagram."
        )


def run_bot():
    telegram_app = Application.builder().token(TOKEN).build()

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Telegram bot started...")
    telegram_app.run_polling()


if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", 10000))
    app_web.run(
        host="0.0.0.0",
        port=port
    )
