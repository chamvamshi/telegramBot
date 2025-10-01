from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    MessageHandler, 
    filters, 
    CommandHandler,
    CallbackQueryHandler
)
from services.storage_service import (
    get_user, add_habit, get_all_habits, get_habit_by_id,
    complete_habit_today, delete_habit, mark_habit_complete
)
from services.ai_response import chat_with_ai
from handlers.start import get_main_keyboard

# Conversation states
HABIT_NAME, HABIT_REMINDER = range(2)

def get_habit_keyboard(has_habits=False):
    if has_habits:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another Habit", callback_data="habit_start")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Start 21-Day Challenge", callback_data="habit_start")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])

def get_habit_action_keyboard(habit_id):
    """Keyboard for individual habit actions"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done Today", callback_data=f"habit_done_{habit_id}")],
        [
            InlineKeyboardButton("🏆 Complete Habit", callback_data=f"habit_finish_{habit_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"habit_delete_{habit_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Habits", callback_data="view_habits")]
    ])

async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main /habits command"""
    chat_id = update.effective_chat.id
    habits = get_all_habits(chat_id)
    
    if not habits:
        await update.message.reply_text(
            "📭 **No Active Habits Yet!**\n\n"
            "Ready to build a life-changing habit in 21 days? 🔄",
            reply_markup=get_habit_keyboard(False)
        )
        return
    
    # Display all habits
    message = f"🔄 **Your Active Habits ({len(habits)}):**\n\n"
    
    for habit in habits:
        progress = (habit['streak'] / 21) * 100
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        days_left = 21 - habit['streak']
        
        message += (
            f"**{habit['id']}. {habit['habit']}**\n"
            f"📊 [{progress_bar}] {int(progress)}%\n"
            f"🔥 Streak: {habit['streak']}/21 days ({days_left} left)\n"
            f"⏰ Reminder: {habit['reminder_time']}\n\n"
        )
    
    message += "\n💡 **Quick Actions:**\n"
    message += "• `/habitinfo <id>` - View habit details\n"
    message += "• `/habitdone <id>` - Mark as done today\n"
    message += "• `/addhabit` - Add new habit"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_habit_keyboard(True)
    )

async def habit_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View specific habit details"""
    if not context.args:
        await update.message.reply_text("Usage: /habitinfo <habit_id>")
        return
    
    try:
        habit_id = int(context.args[0])
        chat_id = update.effective_chat.id
        habit = get_habit_by_id(chat_id, habit_id)
        
        if not habit:
            await update.message.reply_text("❌ Habit not found!")
            return
        
        progress = (habit['streak'] / 21) * 100
        days_left = 21 - habit['streak']
        
        message = (
            f"🔄 **Habit #{habit['id']}**\n\n"
            f"**{habit['habit']}**\n\n"
            f"📊 Progress: {int(progress)}%\n"
            f"🔥 Streak: {habit['streak']} days\n"
            f"🎯 Target: 21 days\n"
            f"⏳ Days Left: {days_left}\n"
            f"📅 Started: {habit['start_date']}\n"
            f"⏰ Reminder: {habit['reminder_time']}"
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_habit_action_keyboard(habit_id)
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID!")

async def habit_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick command to mark habit done"""
    if not context.args:
        await update.message.reply_text("Usage: /habitdone <habit_id>")
        return
    
    try:
        habit_id = int(context.args[0])
        chat_id = update.effective_chat.id
        success, message = complete_habit_today(chat_id, habit_id)
        
        if success:
            habit = get_habit_by_id(chat_id, habit_id)
            if habit:
                ai_prompt = f"Celebrate! Habit: {habit['habit']}, Streak: {habit['streak']}. Short!"
                ai_response = chat_with_ai(ai_prompt, chat_id)
                await update.message.reply_text(f"🎉 {message}\n\n💬 {ai_response}")
        else:
            await update.message.reply_text(f"ℹ️ {message}")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID!")

# Habit creation conversation
async def start_habit_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start habit creation"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "🔄 **What habit do you want to build?**\n\n"
            "Examples:\n"
            "• Wake up at 6 AM\n"
            "• Meditate for 10 minutes\n"
            "• Drink 8 glasses of water\n\n"
            "Type your habit:"
        )
    else:
        await update.message.reply_text(
            "🔄 **What habit do you want to build?**\n\nType your habit:"
        )
    
    return HABIT_NAME

async def habit_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save habit, ask reminder time"""
    context.user_data['habit_name'] = update.message.text
    
    await update.message.reply_text(
        "⏰ **When should I remind you daily?**\n\n"
        "Format: HH:MM (24-hour)\n"
        "Example: 09:00 or 18:30\n\n"
        "Type time (or 'skip' for 9 AM default):"
    )
    return HABIT_REMINDER

async def habit_reminder_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save complete habit"""
    reminder = update.message.text
    
    if reminder.lower() == 'skip':
        reminder = "09:00"
    
    chat_id = update.effective_chat.id
    habit_id = add_habit(chat_id, context.user_data['habit_name'], reminder)
    
    # AI celebration
    ai_prompt = f"Celebrate starting a 21-day habit: {context.user_data['habit_name']}. Short!"
    ai_response = chat_with_ai(ai_prompt, chat_id)
    
    await update.message.reply_text(
        f"🎉 **Habit #{habit_id} Created!**\n\n"
        f"🔄 {context.user_data['habit_name']}\n"
        f"⏰ Reminder: {reminder}\n"
        f"🎯 21-Day Challenge Started!\n\n"
        f"💬 {ai_response}\n\n"
        f"Use `/habitinfo {habit_id}` to view details!",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_habit_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel habit creation"""
    await update.message.reply_text(
        "❌ Cancelled. Use /addhabit anytime!",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# Button handler
async def handle_habit_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all habit button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = query.from_user.id
    
    if data.startswith("habit_done_"):
        habit_id = int(data.split("_")[2])
        success, message = complete_habit_today(chat_id, habit_id)
        
        if success:
            habit = get_habit_by_id(chat_id, habit_id)
            if habit and habit.get('status') != 'completed':
                ai_prompt = f"Celebrate! Habit: {habit['habit']}, Streak: {habit['streak']}. Short!"
                ai_response = chat_with_ai(ai_prompt, chat_id)
                await query.message.reply_text(f"🔥 {message}\n\n💬 {ai_response}")
            else:
                await query.message.reply_text(message)
        else:
            await query.message.reply_text(f"ℹ️ {message}")
    
    elif data.startswith("habit_finish_"):
        habit_id = int(data.split("_")[2])
        success, message = mark_habit_complete(chat_id, habit_id)
        await query.message.reply_text(message)
    
    elif data.startswith("habit_delete_"):
        habit_id = int(data.split("_")[2])
        delete_habit(chat_id, habit_id)
        await query.message.reply_text(f"🗑️ Habit #{habit_id} deleted!")
    
    elif data == "view_habits":
        habits = get_all_habits(chat_id)
        if habits:
            message = f"🔄 **Your Active Habits ({len(habits)}):**\n\n"
            for habit in habits:
                message += f"{habit['id']}. {habit['habit']} - {habit['streak']}/21 days 🔥\n"
            await query.message.reply_text(message, parse_mode='Markdown')

# Conversation handler
habit_conversation = ConversationHandler(
    entry_points=[
        CommandHandler('addhabit', start_habit_creation),
        CallbackQueryHandler(start_habit_creation, pattern='^habit_start$')
    ],
    states={
        HABIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, habit_name_received)],
        HABIT_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, habit_reminder_received)]
    },
    fallbacks=[CommandHandler('cancel', cancel_habit_creation)]
)
