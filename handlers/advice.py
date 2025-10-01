from telegram import Update
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai
from handlers.start import get_main_keyboard


async def advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    topic = " ".join(context.args)
    
    if not topic:
        prompt = "Give me some daily motivation and life advice based on my current goals and situation."
    else:
        prompt = f"I need advice about {topic}. Give me thoughtful, practical guidance."
    
    response = chat_with_ai(prompt, chat_id)
    
    await update.message.reply_text(response, reply_markup=get_main_keyboard())

