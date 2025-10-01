from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # AI generates menu description
    menu_prompt = "Briefly explain the main features available: goals, habits, emotional support, focus help, advice, and check-ins. Keep it concise."
    ai_description = chat_with_ai(menu_prompt, chat_id)
    
    keyboard = [
        [InlineKeyboardButton("🎯 Goals", callback_data="goals"),
         InlineKeyboardButton("🔄 Habits", callback_data="habits")],
        [InlineKeyboardButton("💙 Feel Alone", callback_data="feel"),
         InlineKeyboardButton("🎯 Focus", callback_data="focus")],
        [InlineKeyboardButton("✨ Advice", callback_data="advice"),
         InlineKeyboardButton("📝 Check-in", callback_data="checkin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{ai_description}\n\nChoose what you need help with:",
        reply_markup=reply_markup
    )
