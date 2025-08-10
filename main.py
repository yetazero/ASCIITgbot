import asyncio
import random
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789
CHANNEL_ID = -100123456789
DATA_FILE = "snow_data.json"

WIDTH = 60
HEIGHT = 15
SNOWFLAKE = "*"
INTERVAL = 4.0

frames = []
current_message = None
running = False
message_id = None

def generate_frames():
    snow_positions = [random.randint(0, HEIGHT - 1) for _ in range(WIDTH)]
    result = []
    for frame_num in range(HEIGHT * 2):
        frame = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
        for x in range(WIDTH):
            y = (snow_positions[x] + frame_num) % HEIGHT
            frame[y][x] = SNOWFLAKE
        frame_str = "```\n" + "\n".join("".join(row) for row in frame) + "\n```"
        result.append(frame_str)
    return result

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"message_id": message_id}, f)

def load_data():
    global message_id
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            message_id = data.get("message_id")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("Bot is ready.")

async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_message, frames, running, message_id
    if update.effective_user.id != OWNER_ID:
        return
    frames = generate_frames()
    current_message = await context.bot.send_message(CHANNEL_ID, frames[0], parse_mode="MarkdownV2")
    message_id = current_message.message_id
    save_data()
    running = True
    asyncio.create_task(animate(CHANNEL_ID, context))

async def animate(chat_id, context: ContextTypes.DEFAULT_TYPE):
    global running, current_message, message_id
    frame_index = 0
    while running:
        try:
            frame_index = (frame_index + 1) % len(frames)
            await context.bot.edit_message_text(frames[frame_index], chat_id, message_id, parse_mode="MarkdownV2")
            await asyncio.sleep(INTERVAL)
        except Exception as e:
            if "Retry after" in str(e):
                wait_time = int(str(e).split("Retry after")[1].split()[0])
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(INTERVAL)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    if update.effective_user.id != OWNER_ID:
        return
    running = False

async def on_startup(app: Application):
    global frames, current_message, running
    load_data()
    if message_id:
        frames = generate_frames()
        running = True
        asyncio.create_task(animate(CHANNEL_ID, app))

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("channel", channel))
    app.add_handler(CommandHandler("stop", stop))
    app.post_init = on_startup
    app.run_polling()
