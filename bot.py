from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from config import BOT_TOKEN
from handlers import start, goals, habits
from handlers.goals import goal_conversation, handle_goal_actions
from handlers.habits import habit_conversation, handle_habit_actions
from services.storage_service import load_data, get_all_goals, get_all_habits, delete_goal, delete_habit
from services.ai_response import chat_with_ai
from services.ui_service import render_detailed_progress_screen
import datetime
from datetime import time


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "🎯 My Goals":
        await goals.goals_command(update, context)
    elif text == "🔄 My Habits":
        await habits.habits_command(update, context)
    elif text == "📊 My Progress":
        progress = render_detailed_progress_screen(chat_id)
        await update.message.reply_text(progress, parse_mode='Markdown')
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


# Custom reminder function for each goal/habit at specific times
async def send_goal_reminder(context):
    job = context.job
    chat_id = job.data['chat_id']
    goal = job.data['goal']
    today = datetime.date.today().isoformat()
    
    if goal.get('last_checkin') != today and goal.get('status') == 'active':
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎯 **Goal Reminder**\n\n"
                 f"💭 {goal.get('motivation', 'Stay on track!')}\n\n"
                 f"**Goal:** {goal['goal']}\n"
                 f"🔥 Streak: {goal.get('streak', 0)} days\n"
                 f"🎯 Target: {goal.get('target_days', 30)} days\n\n"
                 f"Mark it done: /goaldone {goal['id']}",
            parse_mode='Markdown'
        )


async def send_habit_reminder(context):
    job = context.job
    chat_id = job.data['chat_id']
    habit = job.data['habit']
    today = datetime.date.today().isoformat()
    
    if habit.get('last_completed') != today and habit.get('status') == 'active':
        days_left = 21 - habit.get('streak', 0)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔄 **Habit Reminder**\n\n"
                 f"**Habit:** {habit['habit']}\n"
                 f"🔥 Streak: {habit.get('streak', 0)}/21 days\n"
                 f"⏳ Days left: {days_left}\n\n"
                 f"Complete it: /habitdone {habit['id']}",
            parse_mode='Markdown'
        )


# Schedule reminders at user-specified times
def schedule_custom_reminders(application):
    """Schedule reminders for each goal/habit at their specific times"""
    data = load_data()
    
    for chat_id_str, user in data.items():
        chat_id = int(chat_id_str)
        
        # Schedule goal reminders
        for goal in user.get('goals', []):
            if isinstance(goal, dict) and goal.get('status') == 'active':
                for reminder_time in goal.get('reminder_times', ['09:00']):
                    try:
                        parts = reminder_time.split(':')
                        if len(parts) == 2:
                            h = int(parts[0])
                            m = int(parts[1])
                            h_str = f"{h:02d}"
                            m_str = f"{m:02d}"
                            normalized_time = f"{h_str}:{m_str}"
                        else:
                            print(f"⚠️ Invalid reminder time format for goal: {reminder_time}")
                            continue
                        print(f"Scheduling goal reminder for chat_id={chat_id}, goal_id={goal['id']}, time={normalized_time}")
                        application.job_queue.run_daily(
                            send_goal_reminder,
                            time=time(hour=h, minute=m),
                            data={'chat_id': chat_id, 'goal': goal},
                            name=f"{chat_id}_goal_{goal['id']}_{normalized_time}"
                        )
                    except Exception as e:
                        print(f"⚠️ Error scheduling goal reminder: {e}")
        
        # Schedule habit reminders
        for habit in user.get('habits', []):
            if isinstance(habit, dict) and habit.get('status') == 'active':
                for reminder_time in habit.get('reminder_times', ['09:00']):
                    try:
                        parts = reminder_time.split(':')
                        if len(parts) == 2:
                            h = int(parts[0])
                            m = int(parts[1])
                            h_str = f"{h:02d}"
                            m_str = f"{m:02d}"
                            normalized_time = f"{h_str}:{m_str}"
                        else:
                            print(f"⚠️ Invalid reminder time format for habit: {reminder_time}")
                            continue
                        print(f"Scheduling habit reminder for chat_id={chat_id}, habit_id={habit['id']}, time={normalized_time}")
                        application.job_queue.run_daily(
                            send_habit_reminder,
                            time=time(hour=h, minute=m),
                            data={'chat_id': chat_id, 'habit': habit},
                            name=f"{chat_id}_habit_{habit['id']}_{normalized_time}"
                        )
                    except Exception as e:
                        print(f"⚠️ Error scheduling habit reminder: {e}")
    
    print(f"✅ Custom reminders scheduled for all users")


# NEW: Delete Goal Command
async def delete_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a goal by ID"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/deletegoal <goal_id>`\n\n"
            "Example: `/deletegoal 1`\n\n"
            "Use `/goals` to see your goal IDs.",
            parse_mode='Markdown'
        )
        return
    
    try:
        goal_id = int(context.args[0])
        chat_id = update.effective_chat.id
        
        # Get goal info before deleting
        from services.storage_service import get_goal_by_id
        goal = get_goal_by_id(chat_id, goal_id)
        
        if not goal:
            await update.message.reply_text(f"❌ Goal #{goal_id} not found!")
            return
        
        # Delete the goal
        delete_goal(chat_id, goal_id)
        
        await update.message.reply_text(
            f"🗑️ **Goal Deleted!**\n\n"
            f"Goal: {goal['goal']}\n"
            f"Streak was: {goal['streak']} days\n\n"
            f"Use `/goals` to see remaining goals.",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID! Please enter a number.")


# NEW: Delete Habit Command
async def delete_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a habit by ID"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/deletehabit <habit_id>`\n\n"
            "Example: `/deletehabit 1`\n\n"
            "Use `/habits` to see your habit IDs.",
            parse_mode='Markdown'
        )
        return
    
    try:
        habit_id = int(context.args[0])
        chat_id = update.effective_chat.id
        
        # Get habit info before deleting
        from services.storage_service import get_habit_by_id
        habit = get_habit_by_id(chat_id, habit_id)
        
        if not habit:
            await update.message.reply_text(f"❌ Habit #{habit_id} not found!")
            return
        
        # Delete the habit
        delete_habit(chat_id, habit_id)
        
        await update.message.reply_text(
            f"🗑️ **Habit Deleted!**\n\n"
            f"Habit: {habit['habit']}\n"
            f"Streak was: {habit['streak']} days\n\n"
            f"Use `/habits` to see remaining habits.",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID! Please enter a number.")


async def set_bot_commands(application):
    commands = [
        BotCommand("start", "🌟 Welcome & Main Menu"),
        BotCommand("menu", "📱 Show Main Menu"),
        BotCommand("goals", "🎯 View All My Goals"),
        BotCommand("addgoal", "➕ Add New Goal"),
        BotCommand("goalinfo", "📊 View Goal Details"),
        BotCommand("goaldone", "✅ Mark Goal Done Today"),
        BotCommand("deletegoal", "🗑️ Delete a Goal"),
        BotCommand("habits", "🔄 View All My Habits"),
        BotCommand("addhabit", "➕ Add New Habit"),
        BotCommand("habitinfo", "📊 View Habit Details"),
        BotCommand("habitdone", "✅ Mark Habit Done Today"),
        BotCommand("deletehabit", "🗑️ Delete a Habit"),
        BotCommand("boost", "💪 Get Motivation Boost"),
        BotCommand("help", "❓ Get Help & Commands"),
        BotCommand("cancel", "❌ Cancel Current Action"),
    ]
    await application.bot.set_my_commands(commands)
    print("📱 Bot commands registered!")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ===== COMMAND HANDLERS =====
    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("menu", start.menu))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("boost", start.boost_command))
    
    # Goal commands
    app.add_handler(CommandHandler("goals", goals.goals_command))
    app.add_handler(CommandHandler("goalinfo", goals.goal_info_command))
    app.add_handler(CommandHandler("goaldone", goals.goal_done_command))
    app.add_handler(CommandHandler("deletegoal", delete_goal_command))  # NEW
    
    # Habit commands
    app.add_handler(CommandHandler("habits", habits.habits_command))
    app.add_handler(CommandHandler("habitinfo", habits.habit_info_command))
    app.add_handler(CommandHandler("habitdone", habits.habit_done_command))
    app.add_handler(CommandHandler("deletehabit", delete_habit_command))  # NEW
    
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
    
    # ===== SCHEDULE CUSTOM REMINDERS AT STARTUP =====
    schedule_custom_reminders(app)
    
    # ===== START BOT =====
    print("=" * 50)
    print("✅ SoulFriend MVP Bot Running!")
    print("=" * 50)
    print("🎯 Multiple Goals with Custom Reminders")
    print("🔄 Multiple Habits with Custom Reminders")
    print("⏰ Reminders at user-specified times")
    print("🤖 AI-powered motivation")
    print("🗑️ Delete commands available")
    print("=" * 50)
    app.run_polling()


if __name__ == "__main__":
    main()
