from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler, 
    filters, 
    ContextTypes
)
from config import BOT_TOKEN
from handlers import start, goals, habits
from handlers.goals import goal_conversation, handle_goal_actions
from handlers.habits import habit_conversation, handle_habit_actions
from services.storage_service import load_data, get_all_goals, get_all_habits
from services.ai_response import chat_with_ai
from services.ui_service import render_detailed_progress_screen
import datetime


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses"""
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "🎯 My Goals":
        await goals.goals_command(update, context)
    
    elif text == "🔄 My Habits":
        await habits.habits_command(update, context)
    
    elif text == "📊 My Progress":
        # Show detailed progress
        progress = render_detailed_progress_screen(chat_id)
        await update.message.reply_text(progress, parse_mode='Markdown')
        
        # AI summary
        goals_list = get_all_goals(chat_id)
        habits_list = get_all_habits(chat_id)
        
        if goals_list or habits_list:
            total_goal_streak = sum(g['streak'] for g in goals_list)
            total_habit_streak = sum(h['streak'] for h in habits_list)
            
            prompt = f"Give me a quick progress summary. Goals: {len(goals_list)} active with {total_goal_streak} total days. Habits: {len(habits_list)} active with {total_habit_streak} total days. Be encouraging and specific! Short message."
            ai_summary = chat_with_ai(prompt, chat_id)
            await update.message.reply_text(f"💬 {ai_summary}")
    
    elif text == "💪 Daily Boost":
        goals_list = get_all_goals(chat_id)
        habits_list = get_all_habits(chat_id)
        
        if not goals_list and not habits_list:
            await update.message.reply_text(
                "💪 Ready to start your journey?\n\n"
                "Set your first goal: /addgoal\n"
                "Start a habit: /addhabit\n\n"
                "Let's make today count! 🚀"
            )
            return
        
        goals_text = ", ".join([g['goal'] for g in goals_list]) if goals_list else "my goals"
        habits_text = ", ".join([h['habit'] for h in habits_list]) if habits_list else "building habits"
        
        prompt = f"Give me motivation! Goals: {goals_text}. Habits: {habits_text}. Short and energetic!"
        ai_msg = chat_with_ai(prompt, chat_id)
        await update.message.reply_text(f"💪 {ai_msg}")


async def send_reminders(context):
    """Send reminders 3x daily to all active users"""
    data = load_data()
    today = datetime.date.today().isoformat()
    reminder_count = 0
    
    for chat_id, user in data.items():
        try:
            # Skip if user has no goals or habits
            if 'goals' not in user and 'habits' not in user:
                continue
            
            # Goal reminders
            if 'goals' in user and isinstance(user['goals'], list):
                for goal in user['goals']:
                    if isinstance(goal, dict) and goal.get('status') == 'active':
                        if goal.get('last_checkin') != today:
                            await context.bot.send_message(
                                chat_id=int(chat_id),
                                text=f"🎯 **Goal Reminder**\n\n"
                                     f"💭 {goal.get('motivation', 'Stay on track!')}\n\n"
                                     f"**Goal:** {goal['goal']}\n"
                                     f"🔥 Streak: {goal.get('streak', 0)} days\n"
                                     f"🎯 Target: {goal.get('target_days', 30)} days\n\n"
                                     f"Mark it done: /goaldone {goal['id']}",
                                parse_mode='Markdown'
                            )
                            reminder_count += 1
            
            # Habit reminders
            if 'habits' in user and isinstance(user['habits'], list):
                for habit in user['habits']:
                    if isinstance(habit, dict) and habit.get('status') == 'active':
                        if habit.get('last_completed') != today:
                            days_left = 21 - habit.get('streak', 0)
                            await context.bot.send_message(
                                chat_id=int(chat_id),
                                text=f"🔄 **Habit Reminder**\n\n"
                                     f"**Habit:** {habit['habit']}\n"
                                     f"🔥 Streak: {habit.get('streak', 0)}/21 days\n"
                                     f"⏳ Days left: {days_left}\n\n"
                                     f"Complete it: /habitdone {habit['id']}",
                                parse_mode='Markdown'
                            )
                            reminder_count += 1
        
        except Exception as e:
            print(f"⚠️ Error sending reminder to {chat_id}: {e}")
    
    print(f"✅ Sent {reminder_count} reminders")


async def set_bot_commands(application):
    """Set bot commands that appear in Telegram menu"""
    commands = [
        BotCommand("start", "🌟 Welcome & Main Menu"),
        BotCommand("menu", "📱 Show Main Menu"),
        BotCommand("goals", "🎯 View All My Goals"),
        BotCommand("addgoal", "➕ Add New Goal"),
        BotCommand("goalinfo", "📊 View Goal Details"),
        BotCommand("goaldone", "✅ Mark Goal Done Today"),
        BotCommand("habits", "🔄 View All My Habits"),
        BotCommand("addhabit", "➕ Add New Habit"),
        BotCommand("habitinfo", "📊 View Habit Details"),
        BotCommand("habitdone", "✅ Mark Habit Done Today"),
        BotCommand("boost", "💪 Get Motivation Boost"),
        BotCommand("help", "❓ Get Help & Commands"),
        BotCommand("cancel", "❌ Cancel Current Action"),
    ]
    await application.bot.set_my_commands(commands)
    print("📱 Bot commands registered in Telegram menu!")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ===== COMMAND HANDLERS =====
    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("menu", start.menu))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("boost", start.boost_command))
    
    # Goals commands
    app.add_handler(CommandHandler("goals", goals.goals_command))
    app.add_handler(CommandHandler("goalinfo", goals.goal_info_command))
    app.add_handler(CommandHandler("goaldone", goals.goal_done_command))
    
    # Habits commands
    app.add_handler(CommandHandler("habits", habits.habits_command))
    app.add_handler(CommandHandler("habitinfo", habits.habit_info_command))
    app.add_handler(CommandHandler("habitdone", habits.habit_done_command))
    
    # ===== CONVERSATION HANDLERS =====
    app.add_handler(goal_conversation)
    app.add_handler(habit_conversation)
    
    # ===== BUTTON HANDLERS =====
    app.add_handler(CallbackQueryHandler(handle_goal_actions, pattern='^goal_'))
    app.add_handler(CallbackQueryHandler(handle_habit_actions, pattern='^habit_'))
    
    # ===== MENU BUTTON HANDLER =====
    app.add_handler(MessageHandler(
        filters.Regex('^(🎯 My Goals|🔄 My Habits|📊 My Progress|💪 Daily Boost)$'),
        handle_menu_buttons
    ))
    
    # ===== SET BOT COMMANDS ON STARTUP =====
    app.post_init = set_bot_commands
    
    # ===== SCHEDULE REMINDERS 3X DAILY =====
    job_queue = app.job_queue
    job_queue.run_daily(send_reminders, time=datetime.time(hour=9, minute=0))   # 9 AM
    job_queue.run_daily(send_reminders, time=datetime.time(hour=14, minute=0))  # 2 PM
    job_queue.run_daily(send_reminders, time=datetime.time(hour=20, minute=0))  # 8 PM
    
    # ===== START BOT =====
    print("=" * 50)
    print("✅ SoulFriend MVP Bot Running!")
    print("=" * 50)
    print("🎯 Multiple Goals Support")
    print("🔄 Multiple Habits Support (21-day challenges)")
    print("⏰ 3x daily reminders (9 AM, 2 PM, 8 PM)")
    print("🤖 AI-powered motivation & conversations")
    print("📱 Bot commands registered in menu")
    print("=" * 50)
    app.run_polling()


if __name__ == "__main__":
    main()
