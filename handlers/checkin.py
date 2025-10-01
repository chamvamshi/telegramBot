from telegram import Update
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai
from services.storage_service import get_user, save_user
from datetime import datetime
from handlers.start import get_main_keyboard


async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mood_text = " ".join(context.args)
    user = get_user(chat_id)
    
    if not mood_text:
        # AI asks for daily check-in
        prompt = "Ask me how I'm doing today and about my progress on goals/habits. Be caring and specific."
        response = chat_with_ai(prompt, chat_id)
    else:
        # Save mood and get AI response
        user["last_mood"] = mood_text
        user["last_checkin"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_user(chat_id, user)
        
        prompt = f"I'm checking in - here's how I'm feeling: {mood_text}. Respond supportively and ask follow-up questions."
        response = chat_with_ai(prompt, chat_id)
    
    await update.message.reply_text(response, reply_markup=get_main_keyboard())

