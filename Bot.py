import os
import threading
import tempfile
import time

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
        "Отправь мне публичную ссылку на Instagram Reel."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "instagram.com" not in text:
        await update.message.reply_text(
            "❌ Пожалуйста, отправь ссылку на Instagram."
        )
        return

    status = await update.message.reply_text(
        "⏳ Получил ссылку!\n"
        "Начинаю обработку..."
    )

    temp_dir = tempfile.mkdtemp()

    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        output_template = os.path.join(
            temp_dir,
            "%(id)s.%(ext)s"
        )

        ydl_opts = {
            "outtmpl": output_template,
            "format": "bestaudio/best",
            "noplaylist": True,

            "quiet": True,
            "no_warnings": True,

            # Повторные попытки при временных ошибках
            "retries": 3,
            "fragment_retries": 3,

            # Небольшая пауза между запросами
            "sleep_interval_requests": 2,

            # Конвертация в MP3
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],

            "ffmpeg_location": ffmpeg_path,

            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 10; K) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/130.0.0.0 Mobile Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        # Небольшая пауза перед обращением к Instagram
        time.sleep(2)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)

        title = info.get("title") or "Instagram Music"

        audio_file = None

        for filename in os.listdir(temp_dir):
            if filename.lower().endswith(".mp3"):
                audio_file = os.path.join(temp_dir, filename)
                break

        if not audio_file:
            raise Exception("MP3 файл не был создан.")

        await status.edit_text(
            "✅ Готово!\n"
            "Отправляю музыку..."
        )

        with open(audio_file, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                title=title[:64],
                performer="Instagram",
            )

        await status.delete()

    except Exception as e:

        error_text = str(e)

        if "429" in error_text or "Too Many Requests" in error_text:
            message = (
                "⚠️ Instagram временно ограничил запросы.\n\n"
                "Попробуй другую публичную ссылку через несколько минут."
            )

        elif "login" in error_text.lower() or "logged" in error_text.lower():
            message = (
                "🔐 Instagram требует авторизацию.\n\n"
                "Попробуй другой публичный Reel."
            )

        elif "private" in error_text.lower():
            message = (
                "🔒 Этот аккаунт или Reel закрытый.\n\n"
                "Отправь публичную ссылку."
            )

        else:
            message = (
                "❌ Не удалось обработать ссылку.\n\n"
                f"Причина: {error_text[:700]}"
            )

        await status.edit_text(message)

    finally:
        # Удаляем временные файлы
        try:
            for filename in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, filename))
            os.rmdir(temp_dir)
        except Exception:
            pass


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

    telegram_app.run_polling(
        stop_signals=None
    )


if __name__ == "__main__":

    # Telegram запускаем в отдельном потоке
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    # Render Web Service
    port = int(os.environ.get("PORT", 10000))

    app_web.run(
        host="0.0.0.0",
        port=port
    )
