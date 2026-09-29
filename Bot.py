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
        "Отправь мне ссылку на Instagram."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "instagram.com" not in text:
        await update.message.reply_text(
            "Пожалуйста, отправь ссылку на Instagram."
        )
        return

    await update.message.reply_text(
        "⏳ Получил ссылку!\n"
        "Начинаю обработку..."
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:

            output_template = os.path.join(temp_dir, "audio.%(ext)s")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "quiet": True,
                "noplaylist": True,
                "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)

            title = info.get("title", "Instagram audio")

            mp3_file = os.path.join(temp_dir, "audio.mp3")

            if not os.path.exists(mp3_file):
                raise Exception("Аудиофайл не найден")

            await update.message.reply_audio(
                audio=open(mp3_file, "rb"),
                title=title[:64],
            )

    except Exception as e:
        print("DOWNLOAD ERROR:", e)

        await update.message.reply_text(
            "❌ Не удалось обработать эту ссылку.\n\n"
            "Попробуй другую публичную ссылку Instagram."
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

    telegram_app.run_polling(stop_signals=None)


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
