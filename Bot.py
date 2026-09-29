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
        "Отправь мне публичную ссылку на Instagram Reel."
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

                "retries": 3,
                "fragment_retries": 3,
                "socket_timeout": 30,

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
                info = ydl.extract_info(text, download=True)

            video_id = info.get("id", "audio")

            mp3_file = os.path.join(
                temp_dir,
                video_id + ".mp3"
            )

            if not os.path.exists(mp3_file):
                files = os.listdir(temp_dir)

                mp3_files = [
                    f for f in files
                    if f.lower().endswith(".mp3")
                ]

                if not mp3_files:
                    raise Exception("MP3 файл не найден.")

                mp3_file = os.path.join(
                    temp_dir,
                    mp3_files[0]
                )

            file_size = os.path.getsize(mp3_file)

            # Ограничиваем размер отправляемого файла
            if file_size > 48 * 1024 * 1024:
                await update.message.reply_text(
                    "❌ Файл слишком большой для отправки в Telegram."
                )
                return

            title = info.get("title") or "Instagram Audio"

            await update.message.reply_audio(
                audio=open(mp3_file, "rb"),
                title=title[:64],
                performer="Instagram",
                caption="🎵 Готово!"
            )

    except yt_dlp.utils.DownloadError as e:

        error_text = str(e)

        if "429" in error_text or "Too Many Requests" in error_text:
            await update.message.reply_text(
                "❌ Instagram временно ограничил запросы.\n\n"
                "Попробуй эту ссылку позже."
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось обработать эту ссылку.\n\n"
                "Попробуй другую публичную ссылку Instagram Reel."
            )

    except Exception as e:

        print("ERROR:", repr(e))

        await update.message.reply_text(
            "❌ Произошла ошибка при обработке ссылки."
        )


def run_bot():

    telegram_app = (
        Application.builder()
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

    print("Telegram bot started!")

    telegram_app.run_polling(
        stop_signals=None
    )


if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    bot_thread.start()

    port = int(
        os.environ.get("PORT", 10000)
    )

    print(
        f"Web server starting on port {port}"
    )

    app_web.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
        )
