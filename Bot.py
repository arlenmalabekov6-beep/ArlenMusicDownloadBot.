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
                "ffmpeg_location": ffmpeg_path,

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128",
                    }
                ],

                "retries": 2,
                "fragment_retries": 2,
                "socket_timeout": 30,

                "sleep_interval_requests": 2,
                "sleep_interval": 2,
                "max_sleep_interval": 5,

                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/140.0.0.0 Safari/537.36"
                    ),
                    "Referer": "https://www.instagram.com/",
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    text,
                    download=True
                )

            video_id = info.get("id", "audio")

            mp3_file = os.path.join(
                temp_dir,
                video_id + ".mp3"
            )

            if not os.path.exists(mp3_file):

                mp3_files = [
                    f
                    for f in os.listdir(temp_dir)
                    if f.lower().endswith(".mp3")
                ]

                if not mp3_files:
                    raise Exception("MP3 файл не найден.")

                mp3_file = os.path.join(
                    temp_dir,
                    mp3_files[0]
                )

            file_size = os.path.getsize(mp3_file)

            if file_size > 48 * 1024 * 1024:
                await update.message.reply_text(
                    "❌ Файл слишком большой для Telegram."
                )
                return

            title = info.get(
                "title",
                "Instagram Audio"
            )

            with open(mp3_file, "rb") as audio_file:

                await update.message.reply_audio(
                    audio=audio_file,
                    title=title[:64],
                    performer="Instagram",
                    caption="🎵 Готово!"
                )

    except yt_dlp.utils.DownloadError as e:

        error_text = str(e)

        print("YT-DLP ERROR:",
