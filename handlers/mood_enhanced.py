
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from database.mood_db import save_mood  # Use your existing function!
from services.limit_checker import can_check_mood, increment_mood_check
from services.ui_service import get_main_menu_keyboard

# Conversation states
MOOD_RATING = 0

# Mood options (YOUR ORIGINAL DESIGN)
MOOD_OPTIONS = {
    '1': {'name': 'Great / Motivated', 'emoji': '😊', 'mood_type': 'great'},
    '2': {'name': 'Good / Calm', 'emoji': '😌', 'mood_type': 'good'},
    '3': {'name': 'Okay / Neutral', 'emoji': '😐', 'mood_type': 'neutral'},
    '4': {'name': 'Stressed / Overwhelmed', 'emoji': '😰', 'mood_type': 'stressed'},
    '5': {'name': 'Lonely / Sad', 'emoji': '😢', 'mood_type': 'sad'},
    '6': {'name': 'Anxious / Worried', 'emoji': '😟', 'mood_type': 'anxious'}
}

async def check_mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mood check with limit enforcement"""
    chat_id = update.effective_chat.id
    
    # Check limit FIRST
    allowed, error_msg = can_check_mood(chat_id)
    
    if not allowed:
        # BLOCKED - Show premium message
        await update.message.reply_text(
            error_msg,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Allowed - show mood options
    mood_text = "💭 **How are you feeling right now?**\n\n**Choose one:**\n"
    for num, mood in MOOD_OPTIONS.items():
        mood_text += f"{num}. {mood['emoji']} {mood['name']}\n"
    mood_text += "\nReply with number (1-6) or /cancel"
    
    keyboard = [['1', '2', '3'], ['4', '5', '6']]
    
    await update.message.reply_text(
        mood_text,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    
    return MOOD_RATING


async def receive_mood_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mood rating and save using YOUR existing database function"""
    chat_id = update.effective_chat.id
    rating_text = update.message.text.strip()
    
    # Validate rating
    if rating_text not in MOOD_OPTIONS:
        await update.message.reply_text(
            "❌ Please select a number between 1-6.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    mood_info = MOOD_OPTIONS[rating_text]
    
    # Save to database using YOUR existing function
    success = save_mood(
        chat_id=chat_id,
        mood=mood_info['mood_type'],
        feeling_notes=mood_info['name'],
        energy_level=int(rating_text)
    )
    
    if success:
        # Increment mood check counter for free users
        increment_mood_check(chat_id)
        
        # Personalized response based on mood
        responses = {
            '1': "🎉 That's wonderful! Keep riding that positive wave! ✨",
            '2': "😌 Glad you're feeling good! Peaceful vibes coming your way. 🌸",
            '3': "😐 Neutral is okay. Sometimes we just exist, and that's fine. 💙",
            '4': "😰 I hear you. Take a deep breath. You've got this. 💪",
            '5': "😢 I'm here for you. It's okay to feel sad. Better days are ahead. 🫂",
            '6': "😟 Anxiety is tough. Try some deep breaths. You're stronger than you think. 🌟"
        }
        
        response = f"{mood_info['emoji']} **Mood Logged:** {mood_info['name']}\n\n{responses[rating_text]}"
        
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Error saving mood. Please try again.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END


async def cancel_mood_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel mood check"""
    await update.message.reply_text(
        "❌ Mood check cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


# Create ConversationHandler
mood_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler('checkmood', check_mood_command),
        MessageHandler(filters.Regex('^💭 Check Mood$'), check_mood_command)
    ],
    states={
        MOOD_RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mood_rating)]
    },
    fallbacks=[CommandHandler('cancel', cancel_mood_check)],
    per_user=True,
    per_chat=True,
    allow_reentry=True
)


def get_mood_handlers_enhanced():
    """Return mood handlers"""
    return [mood_conversation_handler]
