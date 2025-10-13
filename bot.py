from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from config import BOT_TOKEN
from handlers import start, goals, habits
from handlers.timezone_handler import get_timezone_handlers
from handlers.menu_handlers import handle_menu_buttons
from handlers.goals import goal_conversation, edit_goal_conversation, handle_goal_actions
from handlers.habits import add_habit_handler, edit_add_habit_handler, handle_habit_actions
from handlers.admin import admin_stats_command, admin_users_command, admin_broadcast_command
from handlers.premium import handle_premium_callback, premium_command, cancel_premium_command, get_premium_handlers  # 🆕 Import premium handlers, cancel_premium_command
from jobs.scheduled_jobs import get_scheduled_jobs  # 🆕 Import scheduled jobs
from handlers.mood_enhanced import get_mood_handlers_enhanced
from database import load_data, get_all_goals, get_all_habits, delete_goal, delete_habit
from database import get_goal_by_id, get_habit_by_id, get_user_timezone, get_user, save_user
from services.ui_service import get_main_menu_keyboard
from services.ai_response import chat_with_ai
# from services.ui_service import render_detailed_progress_screen  # Not needed
import datetime
from datetime import time
import pytz
import re

# ===== MENU BUTTON HANDLER =====
def get_user_tz_object(chat_id):
    """Get timezone object for user"""
    tz_name = get_user_timezone(chat_id)
    try:
        return pytz.timezone(tz_name)
    except:
        return pytz.UTC

# ===== REMINDER FUNCTIONS (MULTI-TIMEZONE) =====
async def send_goal_reminder(context):
    """Send goal reminder if not completed today"""
    job = context.job
    chat_id = job.data['chat_id']
    goal = job.data['goal']
    
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    today = user_now.date().isoformat()
    
    if goal.get('last_checkin') != today and goal.get('status') == 'active':
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 **GOAL REMINDER** 🔔\n\n"
                 f"💭 {goal.get('motivation', 'Stay on track!')}\n\n"
                 f"**Goal:** {goal['goal']}\n"
                 f"🔥 Streak: {goal.get('streak', 0)} days\n"
                 f"🎯 Target: {goal.get('target_days', 30)} days\n\n"
                 f"Mark it done: /goaldone {goal['id']}",
            parse_mode='Markdown',
            disable_notification=False
        )

async def send_habit_reminder(context):
    """Send habit reminder if not completed today"""
    job = context.job
    chat_id = job.data['chat_id']
    habit = job.data['habit']
    
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    today = user_now.date().isoformat()
    
    if habit.get('last_completed') != today and habit.get('status') == 'active':
        days_left = 21 - habit.get('streak', 0)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 **HABIT REMINDER** 🔔\n\n"
                 f"**Habit:** {habit['habit']}\n"
                 f"🔥 Streak: {habit.get('streak', 0)}/21 days\n"
                 f"⏳ Days left: {days_left}\n\n"
                 f"Complete it: /habitdone {habit['id']}",
            parse_mode='Markdown',
            disable_notification=False
        )

# ===== EOD SUMMARY FUNCTIONS =====
async def send_eod_summary(context):
    """Send End of Day summary"""
    job = context.job
    chat_id = job.data['chat_id']
    
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    today = user_now.date().isoformat()
    
    goals_list = get_all_goals(chat_id)
    habits_list = get_all_habits(chat_id)
    
    if not goals_list and not habits_list:
        return
    
    completed_goals = [g for g in goals_list if g.get('last_checkin') == today]
    missed_goals = [g for g in goals_list if g.get('last_checkin') != today]
    
    completed_habits = [h for h in habits_list if h.get('last_completed') == today]
    missed_habits = [h for h in habits_list if h.get('last_completed') != today]
    
    total_completed = len(completed_goals) + len(completed_habits)
    
    summary = f"📊 **Daily Summary**\n\n"
    
    if total_completed > 0:
        summary += f"Great job on completing {total_completed} {'task' if total_completed == 1 else 'tasks'}!\n\n"
    else:
        summary += f"No tasks completed today.\n\n"
    
    for goal in completed_goals:
        summary += f"✅ {goal['goal']}\n"
    
    for goal in missed_goals:
        summary += f"❌ {goal['goal']}\n"
    
    for habit in completed_habits:
        summary += f"✅ {habit['habit']}\n"
    
    for habit in missed_habits:
        summary += f"❌ {habit['habit']}\n"
    
    missed_count = len(missed_goals) + len(missed_habits)
    
    if missed_count > 0:
        summary += f"\nTomorrow, aim for {missed_count} more {'task' if missed_count == 1 else 'tasks'}."
    else:
        summary += f"\n🎉 Perfect day! Keep it up tomorrow!"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=summary,
        parse_mode='Markdown',
        disable_notification=False
    )

def schedule_eod_summary(application, chat_id, eod_time):
    """Schedule EOD summary for a user"""
    user_tz = get_user_tz_object(chat_id)
    
    try:
        parts = eod_time.split(':')
        if len(parts) == 2:
            h = int(parts[0])
            m = int(parts[1])
            
            current_jobs = application.job_queue.jobs()
            for job in current_jobs:
                if job.name and job.name == f"{chat_id}_eod":
                    job.schedule_removal()
            
            eod_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
            
            application.job_queue.run_daily(
                send_eod_summary,
                time=eod_time_obj,
                data={'chat_id': chat_id},
                name=f"{chat_id}_eod"
            )
            print(f"✅ EOD Summary scheduled for user {chat_id} at {h:02d}:{m:02d} {user_tz.zone}")
            return True
    except Exception as e:
        print(f"❌ Error scheduling EOD: {e}")
        return False

# ===== DYNAMIC REMINDER SCHEDULING =====
def schedule_single_goal_reminder(application, chat_id, goal):
    """Schedule reminders for a single goal immediately"""
    user_tz = get_user_tz_object(chat_id)
    
    for reminder_time in goal.get('reminder_times', ['09:00']):
        try:
            parts = reminder_time.split(':')
            if len(parts) == 2:
                h = int(parts[0])
                m = int(parts[1])
                
                reminder_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
                
                application.job_queue.run_daily(
                    send_goal_reminder,
                    time=reminder_time_obj,
                    data={'chat_id': chat_id, 'goal': goal},
                    name=f"{chat_id}_goal_{goal['id']}_{h:02d}:{m:02d}"
                )
                print(f"✅ AUTO-SCHEDULED: Goal #{goal['id']} reminder at {h:02d}:{m:02d} {user_tz.zone}")
        except Exception as e:
            print(f"❌ Error auto-scheduling goal reminder: {e}")

def schedule_single_habit_reminder(application, chat_id, habit):
    """Schedule reminders for a single habit immediately"""
    user_tz = get_user_tz_object(chat_id)
    
    for reminder_time in habit.get('reminder_times', ['09:00']):
        try:
            parts = reminder_time.split(':')
            if len(parts) == 2:
                h = int(parts[0])
                m = int(parts[1])
                
                reminder_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
                
                application.job_queue.run_daily(
                    send_habit_reminder,
                    time=reminder_time_obj,
                    data={'chat_id': chat_id, 'habit': habit},
                    name=f"{chat_id}_habit_{habit['id']}_{h:02d}:{m:02d}"
                )
                print(f"✅ AUTO-SCHEDULED: Habit #{habit['id']} reminder at {h:02d}:{m:02d} {user_tz.zone}")
        except Exception as e:
            print(f"❌ Error auto-scheduling habit reminder: {e}")

# ===== INITIAL REMINDER SCHEDULING (ON STARTUP) =====
def schedule_custom_reminders(application):
    """Schedule reminders for each user in their timezone on bot startup"""
    data = load_data()
    
    print("\n" + "=" * 70)
    print("⏰ SCHEDULING REMINDERS (MULTI-TIMEZONE SUPPORT)")
    print("=" * 70)
    
    total_reminders = 0
    
    for chat_id_str, user in data.items():
        chat_id = int(chat_id_str)
        
        user_tz = get_user_tz_object(chat_id)
        user_now = datetime.datetime.now(user_tz)
        
        print(f"\n👤 User {chat_id}:")
        print(f"   🌍 Timezone: {user_tz.zone}")
        print(f"   ⏰ Current time: {user_now.strftime('%H:%M:%S %Z')}")
        
        for goal in user.get('goals', []):
            if isinstance(goal, dict) and goal.get('status') == 'active':
                for reminder_time in goal.get('reminder_times', ['09:00']):
                    try:
                        parts = reminder_time.split(':')
                        if len(parts) == 2:
                            h = int(parts[0])
                            m = int(parts[1])
                            
                            reminder_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
                            
                            application.job_queue.run_daily(
                                send_goal_reminder,
                                time=reminder_time_obj,
                                data={'chat_id': chat_id, 'goal': goal},
                                name=f"{chat_id}_goal_{goal['id']}_{h:02d}:{m:02d}"
                            )
                            
                            print(f"   ✅ Goal #{goal['id']} at {h:02d}:{m:02d}")
                            total_reminders += 1
                    except Exception as e:
                        print(f"   ❌ Error scheduling goal {goal.get('id')}: {e}")
        
        for habit in user.get('habits', []):
            if isinstance(habit, dict) and habit.get('status') == 'active':
                for reminder_time in habit.get('reminder_times', ['09:00']):
                    try:
                        parts = reminder_time.split(':')
                        if len(parts) == 2:
                            h = int(parts[0])
                            m = int(parts[1])
                            
                            reminder_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
                            
                            application.job_queue.run_daily(
                                send_habit_reminder,
                                time=reminder_time_obj,
                                data={'chat_id': chat_id, 'habit': habit},
                                name=f"{chat_id}_habit_{habit['id']}_{h:02d}:{m:02d}"
                            )
                            
                            print(f"   ✅ Habit #{habit['id']} at {h:02d}:{m:02d}")
                            total_reminders += 1
                    except Exception as e:
                        print(f"   ❌ Error scheduling habit {habit.get('id')}: {e}")
        
        eod_time = user.get('eod_time', None)
        if eod_time:
            try:
                parts = eod_time.split(':')
                if len(parts) == 2:
                    h = int(parts[0])
                    m = int(parts[1])
                    
                    eod_time_obj = time(hour=h, minute=m, tzinfo=user_tz)
                    
                    application.job_queue.run_daily(
                        send_eod_summary,
                        time=eod_time_obj,
                        data={'chat_id': chat_id},
                        name=f"{chat_id}_eod"
                    )
                    
                    print(f"   📊 EOD Summary at {h:02d}:{m:02d}")
                    total_reminders += 1
            except Exception as e:
                print(f"   ❌ Error scheduling EOD: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ Total reminders scheduled: {total_reminders}")
    print("=" * 70 + "\n")

# ===== EOD COMMANDS =====
async def set_eod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set End of Day summary time"""
    if not context.args:
        await update.message.reply_text(
            "⏰ **Set Your End of Day Summary**\n\n"
            "**Usage:** /seteod HH:MM\n\n"
            "**Examples:**\n"
            "• /seteod 21:00 (9 PM)\n"
            "• /seteod 20:30 (8:30 PM)\n\n"
            "You'll get a daily summary showing:\n"
            "✅ Completed goals/habits\n"
            "❌ Missed goals/habits\n"
            "📊 Daily progress\n"
            "💡 Motivation for tomorrow",
            parse_mode='Markdown'
        )
        return
    
    eod_time = context.args[0].strip()
    
    time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    if not time_pattern.match(eod_time):
        await update.message.reply_text(
            "❌ Invalid time format!\n\n"
            "Please use HH:MM format (e.g., 21:00)",
            parse_mode='Markdown'
        )
        return
    
    chat_id = update.effective_chat.id
    
    # Save to MySQL database
    user = get_user(chat_id)
    user['eod_time'] = eod_time
    save_user(chat_id, user)
    
    success = schedule_eod_summary(context.application, chat_id, eod_time)
    
    if success:
        user_tz = get_user_tz_object(chat_id)
        await update.message.reply_text(
            f"✅ **End of Day Summary Set!**\n\n"
            f"⏰ Time: {eod_time}\n"
            f"🌍 Timezone: {user_tz.zone}\n\n"
            f"You'll receive a daily summary every day at this time! 📊",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to set EOD summary. Please try again.")

async def show_eod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current EOD settings"""
    chat_id = update.effective_chat.id
    
    # Load from MySQL database
    user = get_user(chat_id)
    eod_time = user.get('eod_time', None)
    
    if eod_time:
        user_tz = get_user_tz_object(chat_id)
        await update.message.reply_text(
            f"⏰ **Your End of Day Summary**\n\n"
            f"📊 Time: {eod_time}\n"
            f"🌍 Timezone: {user_tz.zone}\n\n"
            f"To change: /seteod <time>\n"
            f"To test: /testeod",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "📭 **No EOD Summary Set**\n\n"
            "Set one with: /seteod 21:00\n\n"
            "Example: Get daily summary at 9 PM",
            parse_mode='Markdown'
        )

async def test_eod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test EOD summary immediately"""
    chat_id = update.effective_chat.id
    
    async def send_test_eod(context):
        await send_eod_summary(context)
    
    context.application.job_queue.run_once(
        send_test_eod,
        when=2,
        data={'chat_id': chat_id}
    )
    
    await update.message.reply_text(
        "🧪 **Testing EOD Summary...**\n\n"
        "You'll receive your summary in 2 seconds!",
        parse_mode='Markdown'
    )

# ===== DEBUGGING COMMANDS =====
async def test_reminder_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test reminder system"""
    chat_id = update.effective_chat.id
    
    async def send_test_notification(context):
        user_tz = get_user_tz_object(context.job.chat_id)
        user_now = datetime.datetime.now(user_tz)
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f"🔔 **TEST REMINDER** 🔔\n\n"
                 f"✅ Reminders are working!\n\n"
                 f"⏰ Your time: {user_now.strftime('%H:%M:%S')}\n"
                 f"🌍 Timezone: {user_tz.zone}\n"
                 f"📅 Date: {user_now.strftime('%Y-%m-%d')}",
            parse_mode='Markdown',
            disable_notification=False
        )
    
    context.application.job_queue.run_once(
        send_test_notification,
        when=10,
        chat_id=chat_id
    )
    
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    await update.message.reply_text(
        f"⏰ **Test Reminder Scheduled!**\n\n"
        f"🌍 Your timezone: {user_tz.zone}\n"
        f"⏰ Current time: {user_now.strftime('%H:%M:%S')}\n"
        f"📬 Reminder in 10 seconds...",
        parse_mode='Markdown'
    )

async def check_scheduled_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check scheduled reminders"""
    chat_id = update.effective_chat.id
    all_jobs = context.application.job_queue.jobs()
    my_jobs = [job for job in all_jobs if job.name and str(chat_id) in str(job.name)]
    
    if not my_jobs:
        await update.message.reply_text(
            "❌ **No reminders scheduled!**\n\n"
            "Make sure you have active goals/habits with reminder times set.",
            parse_mode='Markdown'
        )
        return
    
    user_tz = get_user_tz_object(chat_id)
    message = f"⏰ **Your Scheduled Reminders ({len(my_jobs)}):**\n\n"
    message += f"🌍 Timezone: {user_tz.zone}\n\n"
    for job in my_jobs:
        message += f"• {job.name}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def show_my_reminder_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show reminder times"""
    chat_id = update.effective_chat.id
    goals_list = get_all_goals(chat_id)
    habits_list = get_all_habits(chat_id)
    
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    
    message = f"⏰ **Your Reminder Times**\n\n"
    message += f"🌍 Timezone: {user_tz.zone}\n"
    message += f"⏰ Current time: {user_now.strftime('%H:%M:%S')}\n\n"
    
    if goals_list:
        message += "**🎯 Goals:**\n"
        for goal in goals_list:
            times = ", ".join(goal.get('reminder_times', ['09:00']))
            message += f"• {goal['goal'][:30]}\n  ⏰ {times}\n\n"
    
    if habits_list:
        message += "**🔄 Habits:**\n"
        for habit in habits_list:
            times = ", ".join(habit.get('reminder_times', ['09:00']))
            message += f"• {habit['habit'][:30]}\n  ⏰ {times}\n\n"
    
    if not goals_list and not habits_list:
        message = "📭 No active goals or habits!"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def show_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show timezone information"""
    chat_id = update.effective_chat.id
    user_tz = get_user_tz_object(chat_id)
    user_now = datetime.datetime.now(user_tz)
    utc_now = datetime.datetime.now(pytz.UTC)
    
    message = (
        f"🌍 **Your Timezone Info:**\n\n"
        f"📍 Timezone: {user_tz.zone}\n"
        f"⏰ Your time: {user_now.strftime('%H:%M:%S')}\n"
        f"📅 Your date: {user_now.strftime('%Y-%m-%d')}\n"
        f"🌐 UTC time: {utc_now.strftime('%H:%M:%S')}\n\n"
        f"Change timezone: /settimezone"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ===== DELETE COMMANDS =====
async def delete_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a goal by ID"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** /deletegoal <goal_id>\n\n"
            "Example: /deletegoal 1\n\n"
            "Use /goals to see your goal IDs.",
            parse_mode='Markdown'
        )
        return
    
    try:
        goal_id = int(context.args[0])
        chat_id = update.effective_chat.id
        goal = get_goal_by_id(chat_id, goal_id)
        
        if not goal:
            await update.message.reply_text(f"❌ Goal #{goal_id} not found!")
            return
        
        current_jobs = context.application.job_queue.jobs()
        for job in current_jobs:
            if job.name and job.name.startswith(f"{chat_id}_goal_{goal_id}_"):
                job.schedule_removal()
        
        delete_goal(chat_id, goal_id)
        
        await update.message.reply_text(
            f"🗑️ **Goal Deleted!**\n\n"
            f"Goal: {goal['goal']}\n"
            f"Streak was: {goal['streak']} days\n\n"
            f"Use /goals to see remaining goals.",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid goal ID! Please enter a number.")

async def delete_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a habit by ID"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** /deletehabit <habit_id>\n\n"
            "Example: /deletehabit 1\n\n"
            "Use /habits to see your habit IDs.",
            parse_mode='Markdown'
        )
        return
    
    try:
        habit_id = int(context.args[0])
        chat_id = update.effective_chat.id
        habit = get_habit_by_id(chat_id, habit_id)
        
        if not habit:
            await update.message.reply_text(f"❌ Habit #{habit_id} not found!")
            return
        
        current_jobs = context.application.job_queue.jobs()
        for job in current_jobs:
            if job.name and job.name.startswith(f"{chat_id}_habit_{habit_id}_"):
                job.schedule_removal()
        
        delete_habit(chat_id, habit_id)
        
        await update.message.reply_text(
            f"🗑️ **Habit Deleted!**\n\n"
            f"Habit: {habit['habit']}\n"
            f"Streak was: {habit['streak']} days\n\n"
            f"Use /habits to see remaining habits.",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid habit ID! Please enter a number.")

# ===== BOT COMMANDS SETUP =====
async def set_bot_commands(application):
    """Set bot commands menu"""
    commands = [
        BotCommand("start", "🌟 Welcome & Main Menu"),
        BotCommand("menu", "📱 Show Main Menu"),
        BotCommand("profile", "👤 View Your Profile"),
        BotCommand("goals", "🎯 View Active Goals"),
        BotCommand("addgoal", "➕ Add New Goal"),
        BotCommand("habits", "🔄 View Active Habits"),
        BotCommand("addhabit", "➕ Add New Habit"),
        BotCommand("checkmood", "💭 Check Your Mood"),
        BotCommand("weeklyreport", "📊 Weekly Progress (Premium)"),
        BotCommand("badges", "🏆 View Badges (Premium)"),
        BotCommand("premium", "💎 Premium Features"),
        BotCommand("help", "❓ Get Help"),
    ]
    await application.bot.set_my_commands(commands)
    print("📱 Bot commands registered!")

# ===== MAIN FUNCTION =====
def main():
    """Initialize and run the bot"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    print("\n" + "=" * 60)
    print("🤖 REGISTERING HANDLERS...")
    print("=" * 60)
    
    # Onboarding
    print("0️⃣ Registering onboarding...")
    from handlers.onboarding import onboarding_conversation
    app.add_handler(onboarding_conversation, group=-1)
    
    # Conversations
    print("1️⃣ Registering conversations...")
    app.add_handler(goal_conversation, group=0)
    app.add_handler(edit_goal_conversation, group=0)
    app.add_handler(add_habit_handler, group=0)
    app.add_handler(edit_add_habit_handler, group=0)
    
    # Basic commands
    print("2️⃣ Registering basic commands...")
    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("menu", start.menu))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("boost", start.boost_command))
    app.add_handler(CommandHandler("profile", start.show_profile))
    
    app.add_handler(CommandHandler("goals", goals.goals_command))
    app.add_handler(CommandHandler("goalinfo", goals.goal_info_command))
    app.add_handler(CommandHandler("goaldone", goals.goal_done_command))
    app.add_handler(CommandHandler("completedgoals", goals.completed_goals_command))
    
    app.add_handler(CommandHandler("habits", habits.habits_command))
    app.add_handler(CommandHandler("habitinfo", habits.habit_info_command))
    app.add_handler(CommandHandler("habitdone", habits.habit_done_command))
    app.add_handler(CommandHandler("completedhabits", habits.completed_habits_command))
    
    # 🆕 Premium commands (clean import)
    print("3️⃣ Registering premium commands...")
    for handler in get_premium_handlers():
        app.add_handler(handler)
    
    
    # Menu button handler
    print("🔘 Registering menu buttons...")
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_menu_buttons
    ), group=2)

  
    
        # Timezone handlers
    print("4️⃣ Registering timezone settings...")
    for handler in get_timezone_handlers():
        app.add_handler(handler)
    
        # Callbacks
    print("4️⃣ Registering callbacks...")
    app.add_handler(CallbackQueryHandler(handle_goal_actions, pattern='^goal_(done|finish|delete)_'), group=1)
    app.add_handler(CallbackQueryHandler(handle_goal_actions, pattern='^view_goals$'), group=1)
    app.add_handler(CallbackQueryHandler(handle_habit_actions, pattern='^habit_(done|finish|delete)_'), group=1)
    app.add_handler(CallbackQueryHandler(handle_habit_actions, pattern='^view_habits$'), group=1)
    
        # Admin commands
    app.add_handler(CommandHandler('admin', admin_stats_command))
    app.add_handler(CommandHandler('adminusers', admin_users_command))
    app.add_handler(CommandHandler('adminbroadcast', admin_broadcast_command))

    
    # Menu buttons
    print("5️⃣ Registering menu buttons...")
    
    
    # 🆕 Schedule jobs (clean import)
    print("6️⃣ Scheduling automated jobs...")
    jobs = get_scheduled_jobs()
    for job_config in jobs:
        if job_config['trigger'] == 'daily':
            app.job_queue.run_daily(
                job_config['callback'],
                time=job_config['time'],
                name=job_config['name']
            )
            print(f"   ✅ Scheduled: {job_config['name']}")
        elif job_config['trigger'] == 'cron':
            app.job_queue.run_daily(
                job_config['callback'],
                time=time(hour=job_config['hour'], minute=job_config['minute'], 
                         tzinfo=job_config['timezone']),
                days=(6,),  # Sunday
                name=job_config['name']
            )
            print(f"   ✅ Scheduled: {job_config['name']}")
    
    # Set commands and run
    app.post_init = set_bot_commands
    schedule_custom_reminders(app)  # Your existing reminder scheduling
    
    print("=" * 60)
    print("✅ SoulFriend Bot Running!")
    print("=" * 60)
    print("🎯 Goal & Habit Tracking")
    print("💎 Premium Features Active")
    print("📊 Automated Reports Scheduled")
    print("🤖 AI-Powered Insights")
    print("=" * 60 + "\n")
    # Premium commands
    print("3️⃣ Registering premium commands...")
    for handler in get_premium_handlers():
      app.add_handler(handler)

# 🆕 ADD THIS SECTION:
# Mood tracking
    print("7️⃣ Registering mood tracking...")
    for handler in get_mood_handlers_enhanced():
     app.add_handler(handler)

    
    app.run_polling()

if __name__ == "__main__":
    main()
