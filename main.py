import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ====== Insert your data here ======
TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 123456789  # Your Telegram user ID
# ===================================

WIDTH = 40
HEIGHT = 10
SNOWFLAKE = "*"
INTERVAL = 2  # seconds

# Global vars
frames = []
current_message = None
running = False

def generate_frames():
    snow_positions = []
    for _ in range(WIDTH):
        snow_positions.append(random.randint(0, HEIGHT - 1))

    result = []
    for frame_num in range(HEIGHT * 2):
        frame = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
        for x in range(WIDTH):
            y = (snow_positions[x] + frame_num) % HEIGHT
            frame[y][x] = SNOWFLAKE
        frame_str = "```\n" + "\n".join("".join(row) for row in frame) + "\n```"
        result.append(frame_str)
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not allowed to use this bot.")
        return
    await update.message.reply_text("Use /snow to start the snow animation.")

async def snow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, frames, current_message
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not allowed to use this bot.")
        return
    if running:
        await update.message.reply_text("❄ Snow animation is already running.")
        return

    running = True
    frames = generate_frames()
    current_message = await update.message.reply_text(frames[0], parse_mode="MarkdownV2")
    asyncio.create_task(animate(update.effective_chat.id, context))

async def animate(chat_id, context: ContextTypes.DEFAULT_TYPE):
    global running, current_message
    try:
        frame_index = 0
        while running:
            try:
                frame_index = (frame_index + 1) % len(frames)
                await current_message.edit_text(frames[frame_index], parse_mode="MarkdownV2")
                await asyncio.sleep(INTERVAL)
            except Exception as e:
                if "Retry after" in str(e):
                    wait_time = int(str(e).split("Retry after")[1].split()[0])
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Edit error: {e}")
                    await asyncio.sleep(INTERVAL)
    except asyncio.CancelledError:
        pass

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not allowed to use this bot.")
        return
    running = False
    await update.message.reply_text("❄ Snow animation stopped.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("snow", snow))
    app.add_handler(CommandHandler("stop", stop))
    app.run_polling()
