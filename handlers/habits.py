from services.limit_checker import can_add_habit
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    filters, CommandHandler, CallbackQueryHandler
)
from database import (
    get_user, add_habit, get_all_habits, get_habit_by_id,
    complete_habit_today, delete_habit, mark_habit_complete,
    update_habit_name, update_habit_streak, update_habit_reminders
)
from services.ai_response import chat_with_ai
from services.ui_service import get_main_menu_keyboard
import re

# Conversation states for habits
HABIT_NAME, HABIT_REMINDERS = range(2)
EDIT_CHOICE, EDIT_NAME, EDIT_DAYS, EDIT_REMINDERS = range(2, 6)



async def add_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔍 add_habit_command called")
    """Start habit creation with STRICT limit check"""
    chat_id = update.effective_chat.id
    
    # CRITICAL: Check limit FIRST
    from services.limit_checker import can_add_habit
    allowed, error_msg = can_add_habit(chat_id)
    
    print(f"🔍 Limit check: allowed={allowed}, chat_id={chat_id}")
    
    if not allowed:
        # BLOCKED - Show premium message
        from services.ui_service import get_main_menu_keyboard
        await update.message.reply_text(
            error_msg, 
            parse_mode='Markdown', 
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END  # STOP HERE
    
    # Allowed - continue
    await update.message.reply_text(
        "🔄 **Create a New Habit**\n\n"
        "What's your habit? (Example: Read 30 minutes)\n\n"
        "Type /cancel to stop",
        parse_mode='Markdown'
    )
    return HABIT_NAME


HABIT_NAME, HABIT_REMINDERS = range(2)
EDIT_CHOICE, EDIT_NAME, EDIT_DAYS, EDIT_REMINDERS = range(2, 6)

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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done Today", callback_data=f"habit_done_{habit_id}")],
        [
            InlineKeyboardButton("✏️ Edit Habit", callback_data=f"edit_habit_{habit_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"habit_delete_{habit_id}")
        ],
        [InlineKeyboardButton("🏆 Complete Habit", callback_data=f"habit_finish_{habit_id}")],
        [InlineKeyboardButton("🔙 Back to Habits", callback_data="view_habits")]
    ])

def get_edit_keyboard(habit_id):
    """Keyboard for choosing what to edit"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_name_{habit_id}")],
        [InlineKeyboardButton("📅 Edit Days/Streak", callback_data=f"edit_days_{habit_id}")],
        [InlineKeyboardButton("⏰ Edit Reminders", callback_data=f"edit_reminders_{habit_id}")],
        [InlineKeyboardButton("🔙 Back to Habit", callback_data=f"back_to_habit_{habit_id}")]
    ])

# ===== HABITS COMMANDS =====
async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View active habits only"""
    chat_id = update.effective_chat.id
    habits = get_all_habits(chat_id, status='active')  # Only active habits
    
    if not habits:
        await update.message.reply_text(
            "📭 **No Active Habits Yet!**\n\n"
            "Ready to build a life-changing habit in 21 days? 🔄\n\n"
            "💡 Tip: Use /completedhabits to see your achievements!",
            parse_mode='Markdown',
            reply_markup=get_habit_keyboard(False)
        )
        return
    
    message = f"🔄 **Your Active Habits ({len(habits)}):**\n\n"
    for habit in habits:
        progress = (habit['streak'] / 21) * 100
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        days_left = 21 - habit['streak']
        reminders = ", ".join(habit.get('reminder_times', ["09:00"]))
        message += (
            f"**{habit['id']}. {habit['habit']}**\n"
            f"📊 [{progress_bar}] {int(progress)}%\n"
            f"🔥 Streak: {habit['streak']}/21 days ({days_left} left)\n"
            f"⏰ Reminders: {reminders}\n\n"
        )
    
    message += "\n💡 **Quick Actions:**\n"
    message += "• /habitinfo <id> - View habit details\n"
    message += "• /habitdone <id> - Mark as done today\n"
    message += "• /addhabit - Add new habit\n"
    message += "• /completedhabits - View completed habits"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_habit_keyboard(True))


async def completed_habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View completed habits"""
    chat_id = update.effective_chat.id
    completed = get_all_habits(chat_id, status='completed')
    
    if not completed:
        await update.message.reply_text(
            "📭 **No Completed Habits Yet!**\n\n"
            "Complete your first 21-day challenge to see it here! 🔄\n\n"
            "💡 Habits auto-complete when you reach 21 days.",
            parse_mode='Markdown'
        )
        return
    
    message = f"✅ **Your Completed Habits ({len(completed)}):**\n\n"
    
    for habit in completed:
        completed_date = habit.get('completed_date', 'Unknown')
        message += (
            f"**{habit['id']}. {habit['habit']}** ✅\n"
            f"🔥 Final Streak: {habit['streak']} days\n"
            f"📅 Completed: {completed_date}\n\n"
        )
    
    message += "\n🎉 **You're building amazing habits! Keep it up!**"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def habit_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /habitinfo <habit_id>")
        return
    
    try:
        habit_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID!")
        return
    
    chat_id = update.effective_chat.id
    habit = get_habit_by_id(chat_id, habit_id)
    
    if not habit:
        await update.message.reply_text("❌ Habit not found!")
        return
    
    progress = (habit['streak'] / 21) * 100
    days_left = 21 - habit['streak']
    reminders = ", ".join(habit.get('reminder_times', ["09:00"]))
    
    status_indicator = "✅ COMPLETED" if habit.get('status') == 'completed' else "🔄 ACTIVE"
    
    message = (
        f"🔄 **Habit #{habit['id']}** {status_indicator}\n\n"
        f"**{habit['habit']}**\n\n"
        f"📊 Progress: {int(progress)}%\n"
        f"🔥 Streak: {habit['streak']} days\n"
        f"🎯 Target: 21 days\n"
        f"⏰ Reminders: {reminders}\n"
        f"⏳ Days Left: {days_left if days_left > 0 else 0}\n"
        f"📅 Started: {habit['start_date']}"
    )
    
    if habit.get('completed_date'):
        message += f"\n🏆 Completed: {habit['completed_date']}"
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown', 
        reply_markup=get_habit_action_keyboard(habit_id)
    )


async def habit_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                # Check if just completed 21 days
                if habit.get('status') == 'completed' and habit['streak'] >= 21:
                    # Special celebration for completion!
                    await update.message.reply_text(
                        f"🎉🎉🎉 **AMAZING!** 🎉🎉🎉\n\n"
                        f"You've completed your 21-day habit: **{habit['habit']}**!\n\n"
                        f"🏆 This habit is now part of who you are!\n"
                        f"🔥 Final streak: 21 days\n\n"
                        f"View all your achievements: /completedhabits",
                        parse_mode='Markdown'
                    )
                else:
                    ai_prompt = f"Celebrate! Habit: {habit['habit']}, Streak: {habit['streak']}. Short!"
                    ai_response = chat_with_ai(ai_prompt, chat_id)
                    await update.message.reply_text(f"🎉 {message}\n\n💬 {ai_response}")
        # 🔥 Check for badge awarding (Premium users only)
        from database.premium_db import is_premium_user, track_daily_progress, get_weekly_stats, award_badge
        
        if is_premium_user(chat_id):
            track_daily_progress(chat_id)
            stats = get_weekly_stats(chat_id)
            if stats:
                total_completed = (stats.get('goals_completed') or 0) + (stats.get('habits_completed') or 0)
                total_tasks = (stats.get('total_goals') or 0) + (stats.get('total_habits') or 0)
                completion_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
                
                badge_msg = ""
                if completion_rate >= 90:
                    award_badge(chat_id, 'soul_diamond', completion_rate)
                    badge_msg = "💎 **Soul Diamond Badge!** 90%+ this week! 🎉"
                elif completion_rate >= 80:
                    award_badge(chat_id, 'soul_gold', completion_rate)
                    badge_msg = "🥇 **Soul Gold Badge!** 80%+ this week! 🎉"
                elif completion_rate >= 50:
                    award_badge(chat_id, 'soul_silver', completion_rate)
                    badge_msg = "🥈 **Soul Silver Badge!** 50%+ this week! 🎉"
                
                if badge_msg:
                    await update.message.reply_text(badge_msg, parse_mode='Markdown')

        else:
            await update.message.reply_text(f"ℹ️ {message}")
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID!")

# ===== HABIT CREATION HANDLERS =====
async def start_habit_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text("🔄 **What habit do you want to build?**\n\nType your habit:")
    else:
        await update.message.reply_text("🔄 **What habit do you want to build?**\n\nType your habit:")
    return HABIT_NAME

async def habit_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['habit_name'] = update.message.text
    await update.message.reply_text(
        "⏰ **When should I remind you each day?**\n\n"
        "Send times separated by commas in HH:MM format\n"
        "Example: 07:00,12:30,19:00\n\n"
        "Or type 'skip' for default 09:00:"
    )
    return HABIT_REMINDERS

async def habit_reminders_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    reminder_times = ["09:00"] if raw.lower() == "skip" else [t.strip() for t in raw.split(",") if t.strip()]
    
    # Check if we have the required data
    if 'habit_name' not in context.user_data:
        await update.message.reply_text(
            "❌ Session expired. Please start again with /addhabit",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    chat_id = update.effective_chat.id
    habit_id = add_habit(chat_id, context.user_data['habit_name'], reminder_times)
    
    # 🔥 Schedule reminder immediately (no restart needed!)
    habit = get_habit_by_id(chat_id, habit_id)
    if habit:
        try:
            from bot import schedule_single_habit_reminder
            schedule_single_habit_reminder(context.application, chat_id, habit)
        except Exception as e:
            print(f"⚠️ Could not auto-schedule reminder: {e}")
    
    ai_prompt = f"Celebrate starting a 21-day habit: {context.user_data['habit_name']}. Short!"
    ai_response = chat_with_ai(ai_prompt, chat_id)
    
    await update.message.reply_text(
        f"🎉 **Habit #{habit_id} Created!**\n\n"
        f"🔄 {context.user_data['habit_name']}\n"
        f"⏰ Reminders: {', '.join(reminder_times)}\n"
        f"🎯 21-Day Challenge Started!\n\n"
        f"💬 {ai_response}\n\n"
        f"✅ Reminder scheduled automatically!",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_habit_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

# ===== EDIT HANDLERS =====
async def start_edit_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit options menu"""
    query = update.callback_query
    await query.answer()
    
    habit_id = int(query.data.split("_")[2])
    chat_id = query.from_user.id
    habit = get_habit_by_id(chat_id, habit_id)
    
    if not habit:
        await query.message.reply_text("❌ Habit not found!")
        return ConversationHandler.END
    
    context.user_data['editing_habit_id'] = habit_id
    
    await query.message.reply_text(
        f"✏️ **Editing: {habit['habit']}**\n\nWhat would you like to edit?",
        parse_mode='Markdown',
        reply_markup=get_edit_keyboard(habit_id)
    )
    return EDIT_CHOICE

async def edit_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing habit name"""
    query = update.callback_query
    await query.answer()
    
    habit_id = int(query.data.split("_")[2])
    context.user_data['editing_habit_id'] = habit_id
    
    chat_id = query.from_user.id
    habit = get_habit_by_id(chat_id, habit_id)
    
    await query.edit_message_text(
        f"✏️ **Current name:** {habit['habit']}\n\n"
        "Enter the new habit name:",
        parse_mode='Markdown'
    )
    return EDIT_NAME

async def edit_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new habit name"""
    new_name = update.message.text
    habit_id = context.user_data.get('editing_habit_id')
    
    if not habit_id:
        await update.message.reply_text("❌ Error: Session lost. Please try again.")
        return ConversationHandler.END
    
    chat_id = update.effective_chat.id
    success = update_habit_name(chat_id, habit_id, new_name)
    
    if success:
        await update.message.reply_text(
            f"✅ Habit name updated to: **{new_name}**",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text("❌ Failed to update habit name.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def edit_days_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing habit streak/days"""
    query = update.callback_query
    await query.answer()
    
    habit_id = int(query.data.split("_")[2])
    context.user_data['editing_habit_id'] = habit_id
    
    chat_id = query.from_user.id
    habit = get_habit_by_id(chat_id, habit_id)
    
    await query.edit_message_text(
        f"📅 **Current streak:** {habit['streak']} days\n\n"
        "Enter new streak value (0-21):",
        parse_mode='Markdown'
    )
    return EDIT_DAYS

async def edit_days_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new habit streak"""
    try:
        new_days = int(update.message.text)
        if not 0 <= new_days <= 21:
            await update.message.reply_text("❌ Please enter a number between 0 and 21.")
            return EDIT_DAYS
        
        habit_id = context.user_data['editing_habit_id']
        chat_id = update.effective_chat.id
        
        success = update_habit_streak(chat_id, habit_id, new_days)
        
        if success:
            habit = get_habit_by_id(chat_id, habit_id)
            status_msg = " 🏆 Habit marked as completed!" if new_days >= 21 else ""
            await update.message.reply_text(
                f"✅ Streak updated to **{new_days} days**{status_msg}",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text("❌ Failed to update streak.")
        
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return EDIT_DAYS

async def edit_reminders_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing habit reminders"""
    query = update.callback_query
    await query.answer()
    
    habit_id = int(query.data.split("_")[2])
    context.user_data['editing_habit_id'] = habit_id
    
    chat_id = query.from_user.id
    habit = get_habit_by_id(chat_id, habit_id)
    current_reminders = ", ".join(habit.get('reminder_times', ["09:00"]))
    
    await query.edit_message_text(
        f"⏰ **Current reminders:** {current_reminders}\n\n"
        "Enter new reminder times in HH:MM format, separated by commas:\n"
        "Example: 07:00,12:30,19:00",
        parse_mode='Markdown'
    )
    return EDIT_REMINDERS

async def edit_reminders_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new habit reminders"""
    raw = update.message.text.strip()
    reminder_times = [t.strip() for t in raw.split(",") if t.strip()]
    
    # Validate time format
    time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    invalid_times = [t for t in reminder_times if not time_pattern.match(t)]
    
    if invalid_times:
        await update.message.reply_text(
            f"❌ Invalid time format: {', '.join(invalid_times)}\n"
            "Please use HH:MM format (e.g., 09:00)"
        )
        return EDIT_REMINDERS
    
    habit_id = context.user_data['editing_habit_id']
    chat_id = update.effective_chat.id
    
    # Remove old reminders
    current_jobs = context.application.job_queue.jobs()
    for job in current_jobs:
        if job.name and job.name.startswith(f"{chat_id}_habit_{habit_id}_"):
            job.schedule_removal()
            print(f"🗑️ Removed old reminder: {job.name}")
    
    success = update_habit_reminders(chat_id, habit_id, reminder_times)
    
    if success:
        # 🔥 Schedule new reminders immediately
        habit = get_habit_by_id(chat_id, habit_id)
        if habit:
            try:
                from bot import schedule_single_habit_reminder
                schedule_single_habit_reminder(context.application, chat_id, habit)
            except Exception as e:
                print(f"⚠️ Could not auto-schedule reminder: {e}")
        
        await update.message.reply_text(
            f"✅ Reminders updated to: **{', '.join(reminder_times)}**\n\n"
            f"New reminders scheduled automatically!",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text("❌ Failed to update reminders.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def back_to_habit_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to habit info screen"""
    query = update.callback_query
    await query.answer()
    habit_id = int(query.data.split("_")[3])
    
    chat_id = query.from_user.id
    habit = get_habit_by_id(chat_id, habit_id)
    
    if not habit:
        await query.message.reply_text("❌ Habit not found!")
        return
    
    progress = (habit['streak'] / 21) * 100
    days_left = 21 - habit['streak']
    reminders = ", ".join(habit.get('reminder_times', ["09:00"]))
    message = (
        f"🔄 **Habit #{habit['id']}**\n\n"
        f"**{habit['habit']}**\n\n"
        f"📊 Progress: {int(progress)}%\n"
        f"🔥 Streak: {habit['streak']} days\n"
        f"🎯 Target: 21 days\n"
        f"⏰ Reminders: {reminders}\n"
        f"⏳ Days Left: {days_left}\n"
        f"📅 Started: {habit['start_date']}"
    )
    
    await query.message.edit_text(
        message, 
        parse_mode='Markdown', 
        reply_markup=get_habit_action_keyboard(habit_id)
    )

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel edit operation"""
    await update.message.reply_text("❌ Edit cancelled.", reply_markup=get_main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

# ===== CALLBACK HANDLERS =====
async def handle_habit_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # ONLY handle specific actions - ignore EVERYTHING else
    if data not in ['view_habits'] and not (
        data.startswith("habit_done_") or 
        data.startswith("habit_finish_") or 
        data.startswith("habit_delete_")
    ):
        return  # Let conversation handler deal with it
    
    await query.answer()
    chat_id = query.from_user.id
    
    if data.startswith("habit_done_"):
        habit_id = int(data.split("_")[2])
        success, message = complete_habit_today(chat_id, habit_id)
        if success:
            habit = get_habit_by_id(chat_id, habit_id)
            if habit:
                # Check if just completed 21 days
                if habit.get('status') == 'completed' and habit['streak'] >= 21:
                    await query.message.reply_text(
                        f"🎉🎉🎉 **AMAZING!** 🎉🎉🎉\n\n"
                        f"You've completed your 21-day habit: **{habit['habit']}**!\n\n"
                        f"🏆 This habit is now part of who you are!\n"
                        f"🔥 Final streak: 21 days\n\n"
                        f"View all your achievements: /completedhabits",
                        parse_mode='Markdown'
                    )
                else:
                    ai_prompt = f"Celebrate! Habit: {habit['habit']}, Streak: {habit['streak']}. Short!"
                    ai_response = chat_with_ai(ai_prompt, chat_id)
                    await query.message.reply_text(f"🔥 {message}\n\n💬 {ai_response}")
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
        habits = get_all_habits(chat_id, status='active')
        if habits:
            message = f"🔄 **Your Active Habits ({len(habits)}):**\n\n"
            for habit in habits:
                message += f"{habit['id']}. {habit['habit']} - {habit['streak']}/21 days 🔥\n"
            await query.message.reply_text(message, parse_mode='Markdown')

# ===== CONVERSATION HANDLERS =====


async def receive_habit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 receive_habit_name called with: {update.message.text}")
    """Receive habit name and ask for reminders"""
    context.user_data['habit_name'] = update.message.text
    await update.message.reply_text(
        "⏰ **When should I remind you each day?**\n\n"
        "Send times separated by commas in HH:MM format\n"
        "Example: 07:00,12:30,19:00\n\n"
        "Or type 'skip' for default 09:00:"
    )
    return HABIT_REMINDERS


async def receive_habit_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 receive_habit_reminders called with: {update.message.text}")
    """Receive reminders and save habit"""
    raw = update.message.text.strip()
    reminder_times = ["09:00"] if raw.lower() == "skip" else [t.strip() for t in raw.split(",") if t.strip()]
    
    if 'habit_name' not in context.user_data:
        await update.message.reply_text(
            "❌ Session expired. Please start again with /addhabit",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    chat_id = update.effective_chat.id

    # CRITICAL: Check limit before saving (in case button bypassed entry point)
    from services.limit_checker import can_add_habit
    allowed, error_msg = can_add_habit(chat_id)
    
    if not allowed:
        # BLOCKED - Show premium message and end conversation
        from services.ui_service import get_main_menu_keyboard
        await update.message.reply_text(
            error_msg,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Allowed - continue saving
        habit_id = add_habithabit_id = add_habit(chat_id, context.user_data['habit_name'], reminder_times)
    
    ai_prompt = f"Celebrate starting a 21-day habit: {context.user_data['habit_name']}. Short!"
    ai_response = chat_with_ai(ai_prompt, chat_id)
    
    await update.message.reply_text(
        f"🎉 **Habit #{habit_id} Created!**\n\n"
        f"🔄 {context.user_data['habit_name']}\n"
        f"⏰ Reminders: {', '.join(reminder_times)}\n"
        f"🎯 21-Day Challenge Started!\n\n"
        f"💬 {ai_response}",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel habit creation"""
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END


add_habit_handler = ConversationHandler(
    entry_points=[
        CommandHandler('addhabit', add_habit_command),
        MessageHandler(filters.Regex('^➕ Add New Habit$'), add_habit_command)
    ],
    states={
        HABIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_habit_name)],
        HABIT_REMINDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_habit_reminders)]
    },
    fallbacks=[CommandHandler('cancel', cancel_habit)],
    per_user=True,
    per_chat=True,
    allow_reentry=True,
    name='add_habit_conversation'
)

edit_add_habit_handler = ConversationHandler(
    entry_points=[
        CommandHandler('addhabit', add_habit_command),
        MessageHandler(filters.Regex('^➕ Add New Habit$'), add_habit_command)
    ],
    states={
        HABIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_habit_name)],
        HABIT_REMINDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_habit_reminders)]
    },
    fallbacks=[CommandHandler('cancel', cancel_habit)],
    per_user=True,
    per_chat=True,
    allow_reentry=True,
    name='add_habit_conversation'
)

