from telegram import Update
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai
from handlers.start import get_main_keyboard


async def feel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    feeling = " ".join(context.args)
    
    if not feeling:
        # AI prompts them to share feelings
        prompt = "I'm feeling a bit down and need someone to talk to. Ask me what's bothering me in a caring way."
        response = chat_with_ai(prompt, chat_id)
    else:
        # AI responds to specific feeling
        prompt = f"I'm feeling {feeling}. Please listen and provide emotional support and practical suggestions."
        response = chat_with_ai(prompt, chat_id)
        
    await update.message.reply_text(response, reply_markup=get_main_keyboard())

