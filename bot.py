import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"[START] chat_id: {chat_id}")
    await update.message.reply_text(f"Zizi 작동 중! chat_id: {chat_id}")


async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    print(f"[MSG] chat_id: {chat_id} | text: {text}")
    await update.message.reply_text(f"받음: {text}")


def main():
    print(f"[BOOT] 토큰: {TELEGRAM_TOKEN[:15]}...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("[BOOT] 폴링 시작")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
