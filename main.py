import logging
import os
import io
from fastapi import FastAPI, Request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7557066777:AAEqm25b5ZOWv9bP8VKnC-9mrhrAcIAWDmA"

MapSizes = {
    "88010a": "Firezone 100",
    "880101": "Bermuda",
    "880116": "Nextera",
    "880119": "Firezone 50",
    "880120": "No Land",
    "88011d": "Solara"
}

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

def find_hex_code(content):
    hex_string = content.hex()
    for code in MapSizes:
        if code in hex_string:
            return code
    return None

def modify_map(content, current_hex, new_hex):
    hex_string = content.hex()
    updated_hex_string = hex_string.replace(current_hex, new_hex)
    return bytes.fromhex(updated_hex_string)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    await update.message.reply_text("Welcome to the Map Size Changer Bot! Send me a .meta or .bytes file to begin.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    file = await update.message.document.get_file()
    file_bytes = io.BytesIO()
    await file.download_to_memory(file_bytes)
    content = file_bytes.getvalue()
    file_name = update.message.document.file_name

    current_hex = find_hex_code(content)
    if current_hex:
        current_map_size = MapSizes[current_hex]
        await update.message.reply_text(f"Current map: {current_map_size}")
        keyboard = [[size] for size in MapSizes.values()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Choose the new map size:", reply_markup=reply_markup)

        context.user_data['file_content'] = content
        context.user_data['current_hex'] = current_hex
        context.user_data['file_name'] = file_name
    else:
        await update.message.reply_text("No valid map size found in the file.")

async def handle_map_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    selected_size = update.message.text
    if selected_size not in MapSizes.values():
        await update.message.reply_text("Invalid map size selected.")
        return

    new_hex = [code for code, name in MapSizes.items() if name == selected_size][0]
    file_content = context.user_data.get('file_content')
    current_hex = context.user_data.get('current_hex')
    file_name = context.user_data.get('file_name')

    if file_content and current_hex:
        modified_content = modify_map(file_content, current_hex, new_hex)
        await update.message.reply_document(document=io.BytesIO(modified_content), filename=file_name)
        await update.message.reply_text(f"Map size changed to {selected_size}.")
        context.user_data.clear()
    else:
        await update.message.reply_text("No file data found.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_file))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_map_size))

@app.post("/")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}
