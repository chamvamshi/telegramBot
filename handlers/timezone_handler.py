"""
Timezone Setting Handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler


# Common timezones with user-friendly names
TIMEZONES = {
    "Asia/Kolkata": "🇮🇳 India (IST)",
    "America/New_York": "🇺🇸 US Eastern",
    "America/Chicago": "🇺🇸 US Central",
    "America/Denver": "🇺🇸 US Mountain",
    "America/Los_Angeles": "🇺🇸 US Pacific",
    "Europe/London": "🇬🇧 UK (GMT)",
    "Europe/Paris": "🇫🇷 France (CET)",
    "Europe/Berlin": "🇩🇪 Germany (CET)",
    "Asia/Dubai": "🇦🇪 UAE (GST)",
    "Asia/Singapore": "🇸🇬 Singapore (SGT)",
    "Asia/Tokyo": "🇯🇵 Japan (JST)",
    "Australia/Sydney": "🇦🇺 Australia (AEDT)",
    "Pacific/Auckland": "🇳🇿 New Zealand (NZDT)",
    "Asia/Shanghai": "🇨🇳 China (CST)",
    "Asia/Hong_Kong": "🇭🇰 Hong Kong (HKT)",
    "UTC": "🌍 UTC (Universal)"
}

async def set_timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show timezone selection"""
    
    # Create buttons for common timezones
    keyboard = []
    for tz, name in TIMEZONES.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"tz_{tz}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌍 **Select Your Timezone**\n\n"
        "Choose your timezone so I can send reminders at the right time!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_timezone_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timezone selection callback"""
    query = update.callback_query
    await query.answer()
    
    # Extract timezone from callback data
    timezone = query.data.replace('tz_', '')
    chat_id = update.effective_chat.id
    
    # Update in database
    from database.connection import get_db_connection
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                UPDATE users SET timezone = %s WHERE chat_id = %s
            """, (timezone, chat_id))
            connection.commit()
            
            timezone_name = TIMEZONES.get(timezone, timezone)
            
            from services.ui_service import get_main_menu_keyboard
            
            await query.edit_message_text(
                f"✅ **Timezone Updated!**\n\n"
                f"Your timezone: {timezone_name}\n\n"
                f"Daily summaries and reminders will be sent according to this timezone.",
                parse_mode='Markdown'
            )
            
            # Send menu
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚙️ Settings updated!",
                reply_markup=get_main_menu_keyboard()
            )
            
        except Exception as e:
            print(f"Error updating timezone: {e}")
            await query.edit_message_text("❌ Error updating timezone. Please try again.")
        finally:
            cursor.close()
            connection.close()
    else:
        await query.edit_message_text("❌ Database connection error.")

def get_timezone_handlers():
    """Return timezone handlers"""
    return [
        CommandHandler('settimezone', set_timezone_command),
        CallbackQueryHandler(handle_timezone_selection, pattern='^tz_')
    ]
