import numpy as np
import matplotlib.pyplot as plt
import io
from scipy.signal import find_peaks

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8541718182:AAH_2oPg4ZfZARcUtsPWyF2rMM2dTL0awI0"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🫀 ECG Analiz", callback_data="ecg"),
            InlineKeyboardButton("💪 EMG Analiz", callback_data="emg"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 Signal Analiz Bot\n\nQaysi signalni analiz qilamiz?",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["signal_type"] = query.data

    await query.edit_message_text(
        f"{query.data.upper()} tanlandi.\nTXT fayl yuboring."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "signal_type" not in context.user_data:
        await update.message.reply_text("Avval /start bosing.")
        return

    signal_type = context.user_data["signal_type"]

    loading = await update.message.reply_text("⏳ Analiz...")

    try:
        document = await update.message.document.get_file()
        file_bytes = await document.download_as_bytearray()

        data = np.loadtxt(io.BytesIO(file_bytes))
        signal = data[:, 5] if data.ndim > 1 else data
        signal = signal - np.mean(signal)

        if signal_type == "ecg":
            peaks, _ = find_peaks(signal, distance=50)
            duration = len(signal) / 250
            bpm = int((len(peaks) / duration) * 60)

            caption = f"🫀 ECG\nYurak urishi: {bpm} BPM"

        else:
            rms = np.sqrt(np.mean(signal**2))
            caption = f"💪 EMG\nRMS: {round(rms,3)}"

        plt.figure(figsize=(10,4))
        plt.plot(signal)
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        await loading.delete()

        await update.message.reply_photo(photo=buf, caption=caption)

    except Exception as e:
        await loading.delete()
        await update.message.reply_text(f"Xato: {e}")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()