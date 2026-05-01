import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Zizi 작동 중! 당신의 chat_id: {chat_id}")


async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"받은 메시지: {update.message.text}")


def main():
    print(f"토큰 확인: {TELEGRAM_TOKEN[:20] if TELEGRAM_TOKEN else 'None'}...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Zizi 봇 시작!")
    app.run_polling()


if __name__ == "__main__":
    main()
