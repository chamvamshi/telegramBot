from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    filters, CommandHandler, CallbackQueryHandler
)
from services.storage_service import (
    get_user, add_goal, get_all_goals, get_goal_by_id,
    complete_goal_today, delete_goal, mark_goal_complete
)
from services.ai_response import chat_with_ai
from handlers.start import get_main_keyboard

# Conversation states (added GOAL_REMINDERS)
GOAL_NAME, GOAL_DAYS, GOAL_MOTIVATION, GOAL_REMINDERS = range(4)

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
            InlineKeyboardButton("🏆 Complete Goal", callback_data=f"goal_finish_{goal_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"goal_delete_{goal_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Goals", callback_data="view_goals")]
    ])

async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    goals = get_all_goals(chat_id)
    if not goals:
        await update.message.reply_text(
            "📭 **No Active Goals Yet!**\n\n"
            "Ready to start your journey? Let's set your first goal! 🎯",
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
    message += "• `/goalinfo <id>` - View goal details\n"
    message += "• `/goaldone <id>` - Mark as done today\n"
    message += "• `/addgoal` - Add new goal"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_goal_keyboard(True))

async def goal_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /goalinfo <goal_id>")
        return
    try:
        goal_id = int(context.args[0])
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
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_goal_action_keyboard(goal_id))
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID!")

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
        else:
            await update.message.reply_text(f"ℹ️ {message}")
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID!")

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
    chat_id = update.effective_chat.id
    goal_id = add_goal(
        chat_id,
        context.user_data['goal_name'],
        context.user_data['goal_days'],
        context.user_data['motivation'],
        reminder_times
    )
    ai_prompt = f"Celebrate that I just set this goal: {context.user_data['goal_name']} for {context.user_data['goal_days']} days. Be excited and encouraging! Short message."
    ai_response = chat_with_ai(ai_prompt, chat_id)
    await update.message.reply_text(
        f"🎉 **Goal #{goal_id} Created!**\n\n"
        f"🎯 {context.user_data['goal_name']}\n"
        f"📅 Target: {context.user_data['goal_days']} days\n"
        f"⏰ Reminders: {', '.join(reminder_times)}\n\n"
        f"💬 {ai_response}",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_goal_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

async def handle_goal_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
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
    fallbacks=[CommandHandler('cancel', cancel_goal_creation)]
)
