"""
Professional Onboarding Module
Beautiful multi-step onboarding for new users
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    filters, CommandHandler, CallbackQueryHandler
)
from database import set_user_profile, is_user_onboarded, get_user, save_user
from services.ui_service import get_main_menu_keyboard
import pytz
import re

# Onboarding states
ASK_NAME, SELECT_COUNTRY, SELECT_TIMEZONE, SET_EOD = range(4)

# ===== COUNTRY SELECTION =====
COUNTRIES = {
    '🇮🇳 India': 'Asia/Kolkata',
    '🇺🇸 USA (East)': 'America/New_York',
    '🇺🇸 USA (West)': 'America/Los_Angeles',
    '🇬🇧 UK': 'Europe/London',
    '🇦🇺 Australia': 'Australia/Sydney',
    '🇨🇦 Canada': 'America/Toronto',
    '🇩🇪 Germany': 'Europe/Berlin',
    '🇫🇷 France': 'Europe/Paris',
    '🇯🇵 Japan': 'Asia/Tokyo',
    '🇨🇳 China': 'Asia/Shanghai',
    '🇧🇷 Brazil': 'America/Sao_Paulo',
    '🇦🇪 UAE': 'Asia/Dubai',
    '🇸🇬 Singapore': 'Asia/Singapore',
}

def get_country_keyboard():
    """Create country selection keyboard (3 columns)"""
    buttons = []
    items = list(COUNTRIES.keys())
    
    for i in range(0, len(items), 3):
        row = [
            InlineKeyboardButton(country, callback_data=f"country_{country}")
            for country in items[i:i+3]
        ]
        buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)

# ===== ONBOARDING START =====
async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding process"""
    chat_id = update.effective_chat.id
    
    if is_user_onboarded(chat_id):
        return ConversationHandler.END
    
    welcome_message = (
        "╔═══════════════════════════╗\n"
        "║   🌟 **WELCOME TO**          ║\n"
        "║   **SOULFRIEND BOT** 🤖      ║\n"
        "╚═══════════════════════════╝\n\n"
        "✨ **Your Personal Growth Companion**\n\n"
        "I'll help you:\n"
        "🎯 Set and achieve goals\n"
        "🔄 Build powerful habits\n"
        "📊 Track your progress\n"
        "💪 Stay motivated daily\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Let's get you set up! It takes just **1 minute**.\n\n"
        "**Step 1 of 4:** What's your name? 👤"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )
    
    return ASK_NAME

# ===== NAME INPUT =====
async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate user's name"""
    name = update.message.text.strip()
    
    if len(name) < 2:
        await update.message.reply_text(
            "❌ Name too short!\n\n"
            "Please enter your real name (at least 2 characters):"
        )
        return ASK_NAME
    
    if len(name) > 50:
        await update.message.reply_text(
            "❌ Name too long!\n\n"
            "Please enter a shorter name (max 50 characters):"
        )
        return ASK_NAME
    
    context.user_data['name'] = name
    
    country_message = (
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Nice to meet you, **{name}**!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Step 2 of 4:** Where are you from? 🌍\n\n"
        f"This helps me send reminders at the right time!"
    )
    
    await update.message.reply_text(
        country_message,
        parse_mode='Markdown',
        reply_markup=get_country_keyboard()
    )
    
    return SELECT_COUNTRY

# ===== COUNTRY & TIMEZONE SELECTION =====
async def receive_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive country selection"""
    query = update.callback_query
    await query.answer()
    
    country = query.data.replace("country_", "")
    timezone = COUNTRIES.get(country)
    
    context.user_data['country'] = country
    context.user_data['timezone'] = timezone
    
    # Get current time in user's timezone
    try:
        user_tz = pytz.timezone(timezone)
        from datetime import datetime
        user_now = datetime.now(user_tz)
        time_str = user_now.strftime('%I:%M %p')
    except:
        time_str = "..."
    
    timezone_message = (
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ **Location Set:** {country}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌍 **Timezone:** {timezone}\n"
        f"⏰ **Your current time:** {time_str}\n\n"
        f"**Step 3 of 4:** Daily Summary 📊\n\n"
        f"Want a **daily summary** of your progress?\n\n"
        f"I'll send you:\n"
        f"✅ Completed goals/habits\n"
        f"❌ Missed tasks\n"
        f"📈 Progress insights\n"
        f"💡 Motivation for tomorrow\n\n"
        f"**When should I send it?**\n"
        f"Type time in **HH:MM** format (24-hour)\n\n"
        f"Examples:\n"
        f"• `21:00` for 9 PM\n"
        f"• `20:30` for 8:30 PM\n"
        f"• `22:00` for 10 PM\n\n"
        f"Or type `skip` to set up later."
    )
    
    await query.edit_message_text(
        timezone_message,
        parse_mode='Markdown'
    )
    
    return SET_EOD

# ===== EOD SUMMARY SETUP =====
async def receive_eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive EOD time"""
    eod_input = update.message.text.strip().lower()
    
    if eod_input == 'skip':
        context.user_data['eod_time'] = None
        await finish_onboarding(update, context)
        return ConversationHandler.END
    
    # Validate time format
    time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    if not time_pattern.match(eod_input):
        await update.message.reply_text(
            "❌ **Invalid time format!**\n\n"
            "Please use **HH:MM** format:\n"
            "• `21:00` for 9 PM\n"
            "• `20:30` for 8:30 PM\n\n"
            "Or type `skip` to set up later.",
            parse_mode='Markdown'
        )
        return SET_EOD
    
    context.user_data['eod_time'] = eod_input
    
    await finish_onboarding(update, context)
    return ConversationHandler.END

# ===== FINISH ONBOARDING =====
async def finish_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete onboarding and save user data"""
    chat_id = update.effective_chat.id
    
    name = context.user_data.get('name')
    country = context.user_data.get('country')
    timezone = context.user_data.get('timezone')
    eod_time = context.user_data.get('eod_time')
    
    # Save to database
    set_user_profile(chat_id, name, country, timezone)
    
    # Save EOD time if set
    if eod_time:
        user = get_user(chat_id)
        user['eod_time'] = eod_time
        save_user(chat_id, user)
    
    # Get user's current time
    try:
        user_tz = pytz.timezone(timezone)
        from datetime import datetime
        user_now = datetime.now(user_tz)
        time_str = user_now.strftime('%I:%M %p')
    except:
        time_str = "..."
    
    # Success message
    success_message = (
        "╔═══════════════════════════════╗\n"
        "║  🎉 **SETUP COMPLETE!** 🎉        ║\n"
        "╚═══════════════════════════════╝\n\n"
        f"**👤 Name:** {name}\n"
        f"**🌍 Location:** {country}\n"
        f"**⏰ Timezone:** {timezone}\n"
        f"**🕐 Current time:** {time_str}\n"
    )
    
    if eod_time:
        success_message += f"**📊 Daily Summary:** {eod_time}\n"
    else:
        success_message += f"**📊 Daily Summary:** Not set (use /seteod)\n"
    
    success_message += (
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**🚀 You're all set!** Let's start your journey!\n\n"
        "**Quick Start:**\n"
        "🎯 Set your first goal: /addgoal\n"
        "🔄 Start a 21-day habit: /addhabit\n"
        "📊 View your progress: Menu → My Progress\n\n"
        "**Need help?**\n"
        "Type /help anytime!\n\n"
        "Let's crush those goals! 💪"
    )
    
    await update.message.reply_text(
        success_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    
    # Schedule EOD summary if set
    if eod_time:
        try:
            from bot import schedule_eod_summary
            schedule_eod_summary(context.application, chat_id, eod_time)
            print(f"✅ EOD scheduled for {name} at {eod_time}")
        except Exception as e:
            print(f"⚠️ Could not schedule EOD: {e}")
    
    context.user_data.clear()

# ===== CANCEL ONBOARDING =====
async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel onboarding"""
    await update.message.reply_text(
        "❌ **Setup cancelled.**\n\n"
        "You can restart anytime with /start",
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END

# ===== CONVERSATION HANDLER =====
onboarding_conversation = ConversationHandler(
    entry_points=[
        CommandHandler('start', start_onboarding)
    ],
    states={
        ASK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
        ],
        SELECT_COUNTRY: [
            CallbackQueryHandler(receive_country, pattern='^country_')
        ],
        SET_EOD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_eod)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_onboarding)
    ],
    per_user=True,
    per_chat=True,
    per_message=False
)
