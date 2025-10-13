"""
Mood Tracking Handler
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

MOOD, FEELING = range(2)

async def check_mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask how user is feeling"""
    await update.message.reply_text(
        "💭 **How are you feeling today?**\n\n"
        "Choose one:\n"
        "1️⃣ Great / Motivated\n"
        "2️⃣ Good / Calm\n"
        "3️⃣ Okay / Neutral\n"
        "4️⃣ Stressed / Overwhelmed\n"
        "5️⃣ Lonely / Sad\n"
        "6️⃣ Anxious / Worried\n\n"
        "Reply with number (1-6):",
        parse_mode='Markdown'
    )
    return MOOD

async def receive_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process mood selection"""
    text = update.message.text.strip()
    
    mood_map = {
        '1': 'great', '2': 'good', '3': 'okay',
        '4': 'stressed', '5': 'lonely', '6': 'anxious'
    }
    
    if text not in mood_map:
        await update.message.reply_text("Please choose 1-6")
        return MOOD
    
    context.user_data['mood'] = mood_map[text]
    
    await update.message.reply_text(
        "Tell me more about it (optional):\n"
        "Or type /skip to finish",
        parse_mode='Markdown'
    )
    return FEELING

async def receive_feeling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save mood and feeling"""
    chat_id = update.effective_chat.id
    mood = context.user_data.get('mood')
    feeling = update.message.text if update.message.text != '/skip' else None
    
    # Save to database
    from database.mood_db import save_mood, save_conversation
    save_mood(chat_id, mood, feeling)
    
    # Get AI response
    from services.ai_response import chat_with_ai
    from database import get_user
    
    user = get_user(chat_id)
    user_name = user.get('name', 'friend') if user else 'friend'
    
    prompt = f"User {user_name} is feeling {mood}. {feeling if feeling else 'No details.'} Give short empathetic response (1-2 sentences)."
    ai_response = chat_with_ai(prompt, chat_id)
    
    await update.message.reply_text(
        f"💚 **Mood logged!**\n\n"
        f"💬 {ai_response}\n\n"
        f"Check weekly insights: /weeklyreport",
        parse_mode='Markdown'
    )
    
    # Save conversation for analysis
    if feeling:
        save_conversation(chat_id, feeling, context='mood_check')
    
    return ConversationHandler.END

async def skip_feeling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip feeling notes"""
    chat_id = update.effective_chat.id
    mood = context.user_data.get('mood')
    
    from database.mood_db import save_mood
    save_mood(chat_id, mood)
    
    await update.message.reply_text(
        "💚 **Mood logged!**\n\n"
        "Check your weekly insights: /weeklyreport",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# Conversation handler
mood_conversation = ConversationHandler(
    entry_points=[CommandHandler('checkmood', check_mood_command)],
    states={
        MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mood)],
        FEELING: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feeling),
            CommandHandler('skip', skip_feeling)
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=False,
    per_chat=True,
    per_user=True
)

def get_mood_handlers():
    """Return mood tracking handlers"""
    return [mood_conversation]
