"""
telegram_bot.py – Beispiel für einen Telegram‑Bot zur Freigabe von Aktionen

Dieser Bot zeigt, wie du einen einfachen Approval‑Flow über Telegram
implementieren kannst. Er lauscht auf Chat‑Befehle, sendet Vorschauen und
wartet auf eine /approve oder /deny‑Antwort. Die konkrete Logik (z. B. das
Ausführen eines Codegen‑Run) wird über Callbacks angebunden.

Abhängigkeiten: python-telegram-bot (siehe requirements). 
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "DEIN_BOT_TOKEN"  # im .env setzen

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! Sende /preview, um eine Vorschau zu erhalten.")

# Dummy-Funktion für die Vorschau
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Hier würde der Codegen-Preview aufgerufen werden
    keyboard = [[InlineKeyboardButton("Approve", callback_data='approve'), InlineKeyboardButton("Deny", callback_data='deny')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hier ist die Vorschau (Dummy)", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == 'approve':
        # Hier realen Codegen-Write auslösen
        await query.edit_message_text("Aktion genehmigt. Code wird geschrieben…")
    else:
        await query.edit_message_text("Aktion abgelehnt.")


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
