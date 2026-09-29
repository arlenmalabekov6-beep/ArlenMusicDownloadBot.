import os
import asyncio
import tempfile
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

import yt_dlp
import imageio_ffmpeg


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")


# =========================
# WEB SERVER ДЛЯ RENDER
# =========================

app_web = Flask(__name__)


@app_web.route("/")
def home():
    return "Music Downloader Bot is running!"


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🎵\n\n"
        "Отправь мне публичную ссылку на Instagram Reel."
    )


# =========================
# СКАЧИВАНИЕ AUDIO
# =========================

def download_audio(url, folder):

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    output_template = os.path.join(
        folder,
        "%(title).80s.%(ext)s"
    )

    options = {
        "format": "bestaudio/best",

        "outtmpl": output_template,

        "ffmpeg_location": ffmpeg_path,

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        # Немного замедляем запросы
        "sleep_interval_requests": 2,
        "sleep_interval": 1,
        "max_sleep_interval": 3,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        downloaded_file = ydl.prepare_filename(info)

        mp3_file = os.path.splitext(downloaded_file)[0] + ".mp3"

        if os.path.exists(mp3_file):
            return mp3_file

        # Иногда расширение может отличаться
        for filename in os.listdir(folder):
            if filename.lower().endswith(".mp3"):
                return os.path.join(folder, filename)

    raise FileNotFoundError("MP3 файл не найден")


# =========================
# ОБРАБОТКА ССЫЛКИ
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    if "instagram.com" not in text:
        await update.message.reply_text(
            "❌ Пожалуйста, отправь ссылку на Instagram."
        )
        return

    await update.message.reply_text(
        "⏳ Получил ссылку!\n"
        "Начинаю обработку..."
    )

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            # Скачивание выполняем отдельно,
            # чтобы бот не зависал во время загрузки
            audio_file = await asyncio.to_thread(
                download_audio,
                text,
                temp_dir
            )

            await update.message.reply_text(
                "🎵 Готово! Отправляю аудио..."
            )

            with open(audio_file, "rb") as audio:

                await update.message.reply_audio(
                    audio=audio,
                    title="Instagram Audio"
                )

    except Exception as error:

        error_text = str(error)

        if "429" in error_text or "Too Many Requests" in error_text:

            await update.message.reply_text(
                "⚠️ Instagram временно ограничил запросы "
                "с нашего сервера.\n\n"
                "Попробуй эту ссылку немного позже."
            )

        elif "login required" in error_text.lower():

            await update.message.reply_text(
                "🔒 Instagram требует авторизацию для этой ссылки.\n\n"
                "Попробуй другую публичную ссылку."
            )

        else:

            await update.message.reply_text(
                "❌ Не удалось обработать ссылку.\n\n"
                "Попробуй другую публичную ссылку."
            )

        print("DOWNLOAD ERROR:", error)


# =========================
# ЗАПУСК TELEGRAM
# =========================

def run_bot():

    telegram_app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

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

    telegram_app.run_polling(
        stop_signals=None
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    bot_thread = threading.Thread(
