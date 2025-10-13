from services.limit_checker import can_add_goal
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    filters, CommandHandler, CallbackQueryHandler
)
from database import (
    get_user, add_goal, get_all_goals, get_goal_by_id,
    complete_goal_today, delete_goal, mark_goal_complete,
    update_goal_name, update_goal_days, update_goal_reminders
)

from services.ai_response import chat_with_ai
from services.ui_service import get_main_menu_keyboard
import re

# Conversation states


async def add_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start goal creation with STRICT limit check"""
    chat_id = update.effective_chat.id
    
    # CRITICAL: Check limit FIRST
    from services.limit_checker import can_add_goal
    allowed, error_msg = can_add_goal(chat_id)
    
    print(f"🔍 Goal limit check: allowed={allowed}, chat_id={chat_id}")
    
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
        "🎯 **Create a New Goal**\n\n"
        "What's your goal? (Example: Learn Python)\n\n"
        "Type /cancel to stop",
        parse_mode='Markdown'
    )
    return GOAL_NAME


GOAL_NAME, GOAL_DAYS, GOAL_MOTIVATION, GOAL_REMINDERS = range(4)
EDIT_GOAL_CHOICE, EDIT_GOAL_NAME, EDIT_GOAL_DAYS, EDIT_GOAL_REMINDERS = range(4, 8)

def get_goal_keyboard(has_goals=False):
    if has_goals:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another Goal", callback_data="goal_start")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Set First Goal", callback_data="goal_start")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])

def get_goal_action_keyboard(goal_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done Today", callback_data=f"goal_done_{goal_id}")],
        [
            InlineKeyboardButton("✏️ Edit Goal", callback_data=f"edit_goal_{goal_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"goal_delete_{goal_id}")
        ],
        [InlineKeyboardButton("🏆 Complete Goal", callback_data=f"goal_finish_{goal_id}")],
        [InlineKeyboardButton("🔙 Back to Goals", callback_data="view_goals")]
    ])

def get_edit_goal_keyboard(goal_id):
    """Keyboard for choosing what to edit in a goal"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Goal Name", callback_data=f"edit_goal_name_{goal_id}")],
        [InlineKeyboardButton("📅 Edit Target Days", callback_data=f"edit_goal_days_{goal_id}")],
        [InlineKeyboardButton("⏰ Edit Reminders", callback_data=f"edit_goal_reminders_{goal_id}")],
        [InlineKeyboardButton("🔙 Back to Goal", callback_data=f"back_to_goal_{goal_id}")]
    ])

# ===== GOAL COMMANDS =====

async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    goals = get_all_goals(chat_id, status='active')  # Only active goals
    
    if not goals:
        await update.message.reply_text(
            "📭 **No Active Goals Yet!**\n\n"
            "Ready to start your journey? Let's set your first goal! 🎯\n\n"
            "💡 Tip: Use /completedgoals to see your achievements!",
            parse_mode='Markdown',
            reply_markup=get_goal_keyboard(False)
        )
        return
    
    message = f"🎯 **Your Active Goals ({len(goals)}):**\n\n"
    for goal in goals:
        progress = (goal['streak'] / goal['target_days']) * 100 if goal['target_days'] else 0
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        reminders = ", ".join(goal.get('reminder_times', ["09:00"]))
        message += (
            f"**{goal['id']}. {goal['goal']}**\n"
            f"📊 [{progress_bar}] {int(progress)}%\n"
            f"🔥 Streak: {goal['streak']}/{goal['target_days']} days\n"
            f"⏰ Reminders: {reminders}\n"
            f"💭 {goal['motivation']}\n\n"
        )
    
    message += "\n💡 **Quick Actions:**\n"
    message += "• /goalinfo <id> - View goal details\n"
    message += "• /goaldone <id> - Mark as done today\n"
    message += "• /addgoal - Add new goal\n"
    message += "• /completedgoals - View completed goals"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_goal_keyboard(True))
    
async def completed_goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View completed goals"""
    chat_id = update.effective_chat.id
    completed = get_all_goals(chat_id, status='completed')
    
    if not completed:
        await update.message.reply_text(
            "📭 **No Completed Goals Yet!**\n\n"
            "Complete your first goal to see it here! 🎯\n\n"
            "💡 Goals auto-complete when you reach the target days.",
            parse_mode='Markdown'
        )
        return
    
    message = f"✅ **Your Completed Goals ({len(completed)}):**\n\n"
    
    for goal in completed:
        completed_date = goal.get('completed_date', 'Unknown')
        message += (
            f"**{goal['id']}. {goal['goal']}** ✅\n"
            f"🔥 Final Streak: {goal['streak']} days\n"
            f"🎯 Target: {goal['target_days']} days\n"
            f"📅 Completed: {completed_date}\n"
            f"💭 {goal.get('motivation', '')}\n\n"
        )
    
    message += "\n🎉 **Amazing work! Keep crushing your goals!**"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def goal_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /goalinfo <goal_id>")
        return
    
    try:
        goal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID!")
        return
    
    chat_id = update.effective_chat.id
    goal = get_goal_by_id(chat_id, goal_id)
    
    if not goal:
        await update.message.reply_text("❌ Goal not found!")
        return
    
    progress = (goal['streak'] / goal['target_days']) * 100 if goal['target_days'] else 0
    days_left = goal['target_days'] - goal['streak']
    reminders = ", ".join(goal.get('reminder_times', ["09:00"]))
    message = (
        f"🎯 **Goal #{goal['id']}**\n\n"
        f"**{goal['goal']}**\n\n"
        f"📊 Progress: {int(progress)}%\n"
        f"🔥 Streak: {goal['streak']} days\n"
        f"🎯 Target: {goal['target_days']} days\n"
        f"⏰ Reminders: {reminders}\n"
        f"⏳ Days Left: {days_left}\n"
        f"📅 Started: {goal['start_date']}\n"
        f"💭 Motivation: {goal['motivation']}"
    )
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown', 
        reply_markup=get_goal_action_keyboard(goal_id)
    )

async def goal_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /goaldone <goal_id>")
        return
    
    try:
        goal_id = int(context.args[0])
        chat_id = update.effective_chat.id
        success, message = complete_goal_today(chat_id, goal_id)
        
        if success:
            goal = get_goal_by_id(chat_id, goal_id)
            ai_prompt = f"Celebrate my progress! Goal: {goal['goal']}, Streak: {goal['streak']} days. Short and enthusiastic!"
            ai_response = chat_with_ai(ai_prompt, chat_id)
            await update.message.reply_text(f"🎉 {message}\n\n💬 {ai_response}")
        # 🔥 Check for badge awarding (Premium users only)
        from database.premium_db import is_premium_user, track_daily_progress, get_weekly_stats, award_badge
        
        if is_premium_user(chat_id):
            # Track progress
            track_daily_progress(chat_id)
            
            # Get weekly stats
            stats = get_weekly_stats(chat_id)
            if stats:
                total_completed = (stats.get('goals_completed') or 0) + (stats.get('habits_completed') or 0)
                total_tasks = (stats.get('total_goals') or 0) + (stats.get('total_habits') or 0)
                completion_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
                
                # Award badge if earned
                badge_msg = ""
                if completion_rate >= 90:
                    award_badge(chat_id, 'soul_diamond', completion_rate)
                    badge_msg = "💎 **Soul Diamond Badge Earned!**You hit 90%+ this week! 🎉"
                elif completion_rate >= 80:
                    award_badge(chat_id, 'soul_gold', completion_rate)
                    badge_msg = "🥇 **Soul Gold Badge Earned!**You hit 80%+ this week! 🎉You hit 80%+ this week! 🎉"
                elif completion_rate >= 50:
                    award_badge(chat_id, 'soul_silver', completion_rate)
                    badge_msg = "🥈 **Soul Silver Badge Earned!**You hit 50%+ this week! 🎉"
                
                if badge_msg:
                    await update.message.reply_text(badge_msg, parse_mode='Markdown')

        else:
            await update.message.reply_text(f"ℹ️ {message}")
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID!")

# ===== GOAL CREATION HANDLERS =====
async def start_goal_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text("🎯 **What's your new goal?**\n\nType your goal:")
    else:
        await update.message.reply_text("🎯 **What's your new goal?**\n\nType your goal:")
    return GOAL_NAME

async def goal_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['goal_name'] = update.message.text
    await update.message.reply_text("📅 **How many days to achieve this?**\n\nType number:")
    return GOAL_DAYS

async def goal_days_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text)
        if days < 1 or days > 365:
            await update.message.reply_text("❌ Please enter between 1-365 days")
            return GOAL_DAYS
        context.user_data['goal_days'] = days
        await update.message.reply_text(
            "💭 **Your daily motivation reminder?**\n\n"
            "Type your motivation (or type 'skip'):"
        )
        return GOAL_MOTIVATION
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")
        return GOAL_DAYS

async def goal_motivation_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    motivation = update.message.text if update.message.text.lower() != 'skip' else ""
    context.user_data['motivation'] = motivation
    await update.message.reply_text(
        "⏰ **When should I remind you each day?**\n\n"
        "Send times separated by commas in HH:MM format\n"
        "Example: 08:00,14:00,20:00\n\n"
        "Or type 'skip' for default 09:00:"
    )
    return GOAL_REMINDERS

async def goal_reminders_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    reminder_times = ["09:00"] if raw.lower() == "skip" else [t.strip() for t in raw.split(",") if t.strip()]
    
    # Check if we have the required data
    if 'goal_name' not in context.user_data or 'goal_days' not in context.user_data:
        await update.message.reply_text(
            "❌ Session expired. Please start again with /addgoal",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    chat_id = update.effective_chat.id
    goal_id = add_goal(
        chat_id,
        context.user_data['goal_name'],
        context.user_data['goal_days'],
        context.user_data.get('motivation', ''),
        reminder_times
    )
    
    # 🔥 NEW: Schedule reminder immediately (no restart needed!)
    goal = get_goal_by_id(chat_id, goal_id)
    if goal:
        try:
            from bot import schedule_single_goal_reminder
            schedule_single_goal_reminder(context.application, chat_id, goal)
        except Exception as e:
            print(f"⚠️ Could not auto-schedule reminder: {e}")
    
    ai_prompt = f"Celebrate that I just set this goal: {context.user_data['goal_name']} for {context.user_data['goal_days']} days. Be excited and encouraging! Short message."
    ai_response = chat_with_ai(ai_prompt, chat_id)
    
    await update.message.reply_text(
        f"🎉 **Goal #{goal_id} Created!**\n\n"
        f"🎯 {context.user_data['goal_name']}\n"
        f"📅 Target: {context.user_data['goal_days']} days\n"
        f"⏰ Reminders: {', '.join(reminder_times)}\n\n"
        f"💬 {ai_response}\n\n"
        f"✅ Reminder scheduled automatically!",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_goal_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

# ===== EDIT GOAL HANDLERS =====
async def start_edit_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit options menu for goal"""
    query = update.callback_query
    await query.answer()
    
    goal_id = int(query.data.split("_")[2])
    chat_id = query.from_user.id
    goal = get_goal_by_id(chat_id, goal_id)
    
    if not goal:
        await query.message.reply_text("❌ Goal not found!")
        return ConversationHandler.END
    
    context.user_data['editing_goal_id'] = goal_id
    
    await query.message.reply_text(
        f"✏️ **Editing: {goal['goal']}**\n\nWhat would you like to edit?",
        parse_mode='Markdown',
        reply_markup=get_edit_goal_keyboard(goal_id)
    )
    return EDIT_GOAL_CHOICE

async def edit_goal_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing goal name"""
    query = update.callback_query
    await query.answer()
    
    goal_id = int(query.data.split("_")[3])
    context.user_data['editing_goal_id'] = goal_id
    
    chat_id = query.from_user.id
    goal = get_goal_by_id(chat_id, goal_id)
    
    await query.edit_message_text(
        f"✏️ **Current goal:** {goal['goal']}\n\n"
        "Enter the new goal description:",
        parse_mode='Markdown'
    )
    return EDIT_GOAL_NAME

async def edit_goal_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new goal name"""
    new_name = update.message.text
    goal_id = context.user_data.get('editing_goal_id')
    
    if not goal_id:
        await update.message.reply_text("❌ Error: Session lost. Please try again.")
        return ConversationHandler.END
    
    chat_id = update.effective_chat.id
    success = update_goal_name(chat_id, goal_id, new_name)
    
    if success:
        await update.message.reply_text(
            f"✅ Goal updated to: **{new_name}**",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text("❌ Failed to update goal.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def edit_goal_days_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing goal target days"""
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split("_")[3])
    context.user_data['editing_goal_id'] = goal_id
    
    chat_id = query.from_user.id
    goal = get_goal_by_id(chat_id, goal_id)
    
    await query.edit_message_text(
        f"📅 **Current target:** {goal['target_days']} days\n\n"
        "Enter new target days (1-365):",
        parse_mode='Markdown'
    )
    return EDIT_GOAL_DAYS

async def edit_goal_days_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new goal target days"""
    try:
        new_days = int(update.message.text)
        if not 1 <= new_days <= 365:
            await update.message.reply_text("❌ Please enter a number between 1 and 365.")
            return EDIT_GOAL_DAYS
        
        goal_id = context.user_data['editing_goal_id']
        chat_id = update.effective_chat.id
        
        # Get current goal status BEFORE update
        goal = get_goal_by_id(chat_id, goal_id)
        old_status = goal.get('status', 'active')
        current_streak = goal.get('streak', 0)
        
        # Update the days
        success = update_goal_days(chat_id, goal_id, new_days)
        
        if success:
            # Get updated goal status AFTER update
            goal = get_goal_by_id(chat_id, goal_id)
            new_status = goal.get('status', 'active')
            
            # Different messages based on status change
            if old_status == 'completed' and new_status == 'active':
                await update.message.reply_text(
                    f"✅ **Target updated to {new_days} days**\n\n"
                    f"🔄 Goal reactivated!\n"
                    f"📊 Current: {current_streak}/{new_days} days\n"
                    f"⏳ {new_days - current_streak} days left to complete!",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
            elif new_status == 'completed':
                await update.message.reply_text(
                    f"✅ **Target updated to {new_days} days**\n\n"
                    f"🏆 Goal already completed!\n"
                    f"(Streak: {current_streak} days)",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"✅ Target days updated to **{new_days} days**\n\n"
                    f"📊 Progress: {current_streak}/{new_days} days",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await update.message.reply_text("❌ Failed to update target days.")
        
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return EDIT_GOAL_DAYS


async def edit_goal_reminders_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing goal reminders"""
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split("_")[3])
    context.user_data['editing_goal_id'] = goal_id
    
    chat_id = query.from_user.id
    goal = get_goal_by_id(chat_id, goal_id)
    current_reminders = ", ".join(goal.get('reminder_times', ["09:00"]))
    
    await query.edit_message_text(
        f"⏰ **Current reminders:** {current_reminders}\n\n"
        "Enter new reminder times in HH:MM format, separated by commas:\n"
        "Example: 07:00,12:30,19:00",
        parse_mode='Markdown'
    )
    return EDIT_GOAL_REMINDERS

async def edit_goal_reminders_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new goal reminders"""
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
        return EDIT_GOAL_REMINDERS
    
    goal_id = context.user_data['editing_goal_id']
    chat_id = update.effective_chat.id
    
    # Remove old reminders
    current_jobs = context.application.job_queue.jobs()
    for job in current_jobs:
        if job.name and job.name.startswith(f"{chat_id}_goal_{goal_id}_"):
            job.schedule_removal()
            print(f"🗑️ Removed old reminder: {job.name}")
    
    success = update_goal_reminders(chat_id, goal_id, reminder_times)
    
    if success:
        # 🔥 NEW: Schedule new reminders immediately
        goal = get_goal_by_id(chat_id, goal_id)
        if goal:
            try:
                from bot import schedule_single_goal_reminder
                schedule_single_goal_reminder(context.application, chat_id, goal)
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

async def back_to_goal_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to goal info screen"""
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split("_")[3])
    
    chat_id = query.from_user.id
    goal = get_goal_by_id(chat_id, goal_id)
    
    if not goal:
        await query.message.reply_text("❌ Goal not found!")
        return
    
    progress = (goal['streak'] / goal['target_days']) * 100 if goal['target_days'] else 0
    days_left = goal['target_days'] - goal['streak']
    reminders = ", ".join(goal.get('reminder_times', ["09:00"]))
    message = (
        f"🎯 **Goal #{goal['id']}**\n\n"
        f"**{goal['goal']}**\n\n"
        f"📊 Progress: {int(progress)}%\n"
        f"🔥 Streak: {goal['streak']} days\n"
        f"🎯 Target: {goal['target_days']} days\n"
        f"⏰ Reminders: {reminders}\n"
        f"⏳ Days Left: {days_left}\n"
        f"📅 Started: {goal['start_date']}\n"
        f"💭 Motivation: {goal['motivation']}"
    )
    
    await query.message.edit_text(
        message, 
        parse_mode='Markdown', 
        reply_markup=get_goal_action_keyboard(goal_id)
    )

async def cancel_goal_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel goal edit operation"""
    await update.message.reply_text("❌ Edit cancelled.", reply_markup=get_main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

# ===== CALLBACK HANDLERS =====
async def handle_goal_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # DON'T answer or handle edit callbacks
    if "edit" in data or "back_to" in data:
        return
    
    await query.answer()
    chat_id = query.from_user.id
    
    if data.startswith("goal_done_"):
        goal_id = int(data.split("_")[2])
        success, message = complete_goal_today(chat_id, goal_id)
        if success:
            goal = get_goal_by_id(chat_id, goal_id)
            ai_prompt = f"Celebrate! Goal: {goal['goal']}, Streak: {goal['streak']}. Short!"
            ai_response = chat_with_ai(ai_prompt, chat_id)
            await query.message.reply_text(f"🎉 {message}\n\n💬 {ai_response}")
        else:
            await query.message.reply_text(f"ℹ️ {message}")
    
    elif data.startswith("goal_finish_"):
        goal_id = int(data.split("_")[2])
        success, message = mark_goal_complete(chat_id, goal_id)
        await query.message.reply_text(message)
    
    elif data.startswith("goal_delete_"):
        goal_id = int(data.split("_")[2])
        delete_goal(chat_id, goal_id)
        await query.message.reply_text(f"🗑️ Goal #{goal_id} deleted!")
    
    elif data == "view_goals":
        goals = get_all_goals(chat_id)
        if goals:
            message = f"🎯 **Your Active Goals ({len(goals)}):**\n\n"
            for goal in goals:
                message += f"{goal['id']}. {goal['goal']} - {goal['streak']}/{goal['target_days']} days 🔥\n"
            await query.message.reply_text(message, parse_mode='Markdown')

# ===== CONVERSATION HANDLERS =====
goal_conversation = ConversationHandler(
    entry_points=[
        CommandHandler('addgoal', start_goal_creation),
        CallbackQueryHandler(start_goal_creation, pattern='^goal_start$')
    ],
    states={
        GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_name_received)],
        GOAL_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_days_received)],
        GOAL_MOTIVATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_motivation_received)],
        GOAL_REMINDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_reminders_received)]
    },
    fallbacks=[CommandHandler('cancel', cancel_goal_creation)],
    per_user=True,
    per_chat=True,
    per_message=False
)

edit_goal_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_edit_goal, pattern='^edit_goal_[0-9]+$')
    ],
    states={
        EDIT_GOAL_CHOICE: [
            CallbackQueryHandler(edit_goal_name_start, pattern='^edit_goal_name_[0-9]+$'),
            CallbackQueryHandler(edit_goal_days_start, pattern='^edit_goal_days_[0-9]+$'),
            CallbackQueryHandler(edit_goal_reminders_start, pattern='^edit_goal_reminders_[0-9]+$'),
            CallbackQueryHandler(back_to_goal_info, pattern='^back_to_goal_[0-9]+$')
        ],
        EDIT_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_goal_name_received)],
        EDIT_GOAL_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_goal_days_received)],
        EDIT_GOAL_REMINDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_goal_reminders_received)]
    },
    fallbacks=[CommandHandler('cancel', cancel_goal_edit)],
    per_user=True,
    per_chat=True,
    per_message=False
)
