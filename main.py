import os
import tempfile
from telegram import *
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import ffmpeg

# Токен вашего Telegram бота
TOKEN = "7787818513:AAEZwJ-6tl1B7NN_GdgL0P1GqXWiqVKLEBU"

# Максимальный размер выходного файла (в байтах)
MAX_FILE_SIZE = 256 * 1024  # 256 KB


async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем файл из сообщения
    if update.message.animation or update.message.video:
        file_id = update.message.animation.file_id if update.message.animation else update.message.video.file_id
        file = await context.bot.get_file(file_id)

        # Создаем временные файлы для входных и выходных данных
        temp_in_path = tempfile.NamedTemporaryFile(suffix=".input").name
        temp_out_path = tempfile.NamedTemporaryFile(suffix=".webm").name

        try:
            # Скачиваем видео/GIF во временный файл
            await file.download_to_drive(temp_in_path)

            # Конвертируем видео в WEBM
            convert_to_webm(temp_in_path, temp_out_path, MAX_FILE_SIZE)

            # Отправляем конвертированный файл пользователю
            with open(temp_out_path, 'rb') as webm_file:
                await update.message.reply_document(document=webm_file, filename="output.webm")

        except Exception as e:
            # Обработка ошибок
            await update.message.reply_text(f"Произошла ошибка при обработке файла: {e}")

        finally:
            # Очистка временных файлов
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

    else:
        await update.message.reply_text("Пожалуйста, отправьте GIF или видео.")


def convert_to_webm(input_path, output_path, max_size):
    # Начальные параметры для конвертации
    resolution = None
    crf = 23  # Начальное значение CRF для качества

    while True:
        try:
            # Создаем поток обработки видео через FFmpeg
            (
                ffmpeg.input(input_path)
                .output(
                    output_path,
                    vcodec='libvpx-vp9',
                    crf=crf,
                    preset='fast',
                    vf=f"scale={resolution}" if resolution else None,
                    f='webm'
                )
                .run(overwrite_output=True)
            )

            # Проверяем размер выходного файла
            if os.path.getsize(output_path) <= max_size:
                break

            # Если файл слишком большой, снижаем качество или разрешение
            if not resolution:
                resolution = "1280:-1"  # Начинаем с Full HD
            elif resolution == "1280:-1":
                resolution = "640:-1"  # Переключаемся на HD
            elif resolution == "640:-1":
                resolution = "320:-1"  # Переключаемся на SD
            else:
                crf += 2  # Увеличиваем сжатие если разрешение уже минимальное

        except ffmpeg.Error as e:
            print(f"Ошибка FFmpeg: {e}")
            raise


def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчик сообщений с видео/GIF
    application.add_handler(MessageHandler(filters.VIDEO | filters.ANIMATION, process_video))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
