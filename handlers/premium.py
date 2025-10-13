
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from database.premium_db import is_premium_user, activate_demo_trial

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium features and free trial"""
    chat_id = update.effective_chat.id
    
    is_premium = is_premium_user(chat_id)
    
    if is_premium:
        # Already premium
        await update.message.reply_text(
            "💎 **You're Premium!**\n\n"
            "Enjoying all unlimited features:\n"
            "✅ Unlimited goals & habits\n"
            "✅ Unlimited mood check-ins\n"
            "✅ Full progress tracking\n\n"
            "Thank you for being an early supporter! 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Show free trial offer
    message = (
        "💎 **Unlock Premium Features!**\n\n"
        "🚀 **Available NOW:**\n"
        "• ♾️ **Unlimited** goals & habits\n"
        "• 💭 **Unlimited** mood check-ins\n"
        "• 📊 Daily progress tracking\n"
        "• 🔔 Smart reminders\n"
        "• ⭐ Priority support\n\n"
        "🎁 **Coming in v2.0:**\n"
        "• 📈 Weekly AI insights\n"
        "• 🏆 Achievement badges\n"
        "• 📊 Advanced analytics\n"
        "• 🎯 Personalized coaching\n\n"
        "💰 **Pricing** (Coming Soon):\n"
        "After trial: ₹99/month or ₹999/year\n\n"
        "🎉 **FREE 7-Day Trial** - No credit card needed!\n\n"
        "Try all premium features, completely free!"
    )
    
    keyboard = [[
        InlineKeyboardButton("🎁 Start Free 7-Day Trial", callback_data='premium_trial')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle premium button clicks"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    if query.data == 'premium_trial':
        # Activate 7-day free trial
        success, message = activate_demo_trial(chat_id)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown'
        )


async def cancel_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel premium (for testing)"""
    chat_id = update.effective_chat.id
    
    from database.premium_db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM premium_users WHERE chat_id = %s', (chat_id,))
        cursor.execute('DELETE FROM premium_subscriptions WHERE chat_id = %s', (chat_id,))
        conn.commit()
        
        await update.message.reply_text(
            "✅ **Premium Cancelled**\n\n"
            "You're now a FREE user.\n\n"
            "Free limits:\n"
            "• 3 goals max\n"
            "• 3 habits max\n"
            "• 2 mood checks/day\n\n"
            "To try premium: /premium",
            parse_mode='Markdown'
        )
    finally:
        cursor.close()
        conn.close()


def get_premium_handlers():
    """Return list of premium handlers"""
    return [
        CommandHandler('premium', premium_command),
        CommandHandler('cancelpremium', cancel_premium_command),
        CallbackQueryHandler(handle_premium_callback, pattern='^premium_')
    ]
