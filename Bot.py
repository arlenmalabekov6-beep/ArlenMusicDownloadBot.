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

app_web = Flask(__name__)


@app_web.route("/")
def home():
    return "Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🎵\n\n"
        "Отправь мне ссылку на публичный Instagram Reel."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

        with tempfile.TemporaryDirectory() as temp_dir:

            output_template = os.path.join(
                temp_dir,
                "%(id)s.%(ext)s"
            )

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            ydl_opts = {

                "format": "bestaudio/best",

                "outtmpl": output_template,

                "noplaylist": True,

                "quiet": True,

                "no_warnings": True,

                "ffmpeg_location":
