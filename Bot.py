import os
import threading
import tempfile

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

import yt_dlp
import imageio_ffmpeg


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в Environment Variables")


# =========================
# WEB SERVER FOR RENDER
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Music Downloader Bot is running!"


# =========================
# TELEGRAM /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🎵\n\n"
        "Отправь мне публичную ссылку на Instagram Reel."
    )


# =========================
# INSTAGRAM DOWNLOAD
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if "instagram.com" not in text:
        await update.message.reply_text(
            "❗ Отправь ссылку на Instagram Reel."
        )
        return

    await update.message.reply_text(
        "⏳ Получил ссылку!\n"
        "Начинаю обработку..."
    )

    try:

       
