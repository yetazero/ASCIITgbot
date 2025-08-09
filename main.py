# -*- coding: utf-8 -*-
import logging
import asyncio
import random

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import RetryAfter

# ===== SETTINGS =====
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
OWNER_ID = 123456789          # Replace with your Telegram ID

WIDTH = 40
HEIGHT = 20

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Snowflakes data
snowflakes = []
chat_animation_jobs = {}

def generate_snow_frame():
    """Generate the next snow animation frame."""
    global snowflakes
    snowflakes = [(x, y + 1) for (x, y) in snowflakes if y + 1 < HEIGHT]
    for _ in range(random.randint(2, 6)):
        snowflakes.append((random.randint(0, WIDTH - 1), 0))
    frame = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for (x, y) in snowflakes:
        frame[y][x] = "*"
    return "\n".join("".join(row) for row in frame)

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return
    await update.message.reply_text(
        "❄ Hello! I can show a falling snow animation.\n"
        "Use /snow to start.\n"
        "Use /stop to stop."
    )

async def animate_task(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]

    try:
        frame = generate_snow_frame()
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"```\n{frame}\n```",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except RetryAfter as e:
        delay = int(e.retry_after) + 1
        logger.warning(f"Flood control triggered: waiting {delay} seconds")
        await asyncio.sleep(delay)

    except Exception as e:
        logger.error(f"Error updating animation: {e}")
        context.job.schedule_removal()
        chat_animation_jobs.pop(chat_id, None)

async def snow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    chat_id = update.effective_chat.id

    if chat_id in chat_animation_jobs:
        chat_animation_jobs[chat_id].schedule_removal()
        del chat_animation_jobs[chat_id]

    try:
        frame = generate_snow_frame()
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"```\n{frame}\n```",
            parse_mode=ParseMode.MARKDOWN_V2
        )

        job_data = {"chat_id": chat_id, "message_id": message.message_id}
        job = context.job_queue.run_repeating(animate_task, interval=1.0, first=1.0, data=job_data)
        chat_animation_jobs[chat_id] = job

    except Exception as e:
        logger.error(f"Error starting animation: {e}")
        await update.message.reply_text(f"Error starting animation: {e}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    chat_id = update.effective_chat.id
    if chat_id in chat_animation_jobs:
        chat_animation_jobs[chat_id].schedule_removal()
        del chat_animation_jobs[chat_id]
        await update.message.reply_text("⛔ Animation stopped.")
    else:
        await update.message.reply_text("No animation is running.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("snow", snow))
    application.add_handler(CommandHandler("stop", stop))
    application.run_polling()

if __name__ == "__main__":
    main()
