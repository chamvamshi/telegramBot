from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai
from services.ui_service import render_main_menu
from services.storage_service import get_user, save_user


def get_main_keyboard():
    """Persistent main menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 My Goals"), KeyboardButton(text="🔄 My Habits")],
            [KeyboardButton(text="📊 My Progress"), KeyboardButton(text="💪 Daily Boost")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message when user starts the bot"""
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "friend"
    
    # Initialize user if first time
    user = get_user(chat_id)
    if not user or 'goals' not in user:
        user = {
            'name': user_name,
            'user_id': chat_id,
            'created_at': str(update.message.date),
            'goals': [],
            'habits': []
        }
        save_user(chat_id, user)
    
    # Render beautiful main screen
    main_screen = render_main_menu(chat_id, user_name)
    await update.message.reply_text(main_screen, parse_mode='Markdown')
    
    # AI personalized welcome
    welcome_prompt = f"""Welcome {user_name} to SoulFriend, an accountability bot. 
    Be warm and friendly. Briefly mention you can help with:
    - Setting and tracking goals
    - Building 21-day habits
    - Daily motivation and reminders
    Keep it short, encouraging, and personal. Use their name."""
    
    ai_welcome = chat_with_ai(welcome_prompt, chat_id)
    
    # Send welcome + persistent keyboard
    await update.message.reply_text(
        f"👋 {ai_welcome}\n\n"
        "🚀 **Quick Start:**\n"
        "• Use buttons below for quick access\n"
        "• Type / to see all commands\n"
        "• Use /help anytime for assistance\n\n"
        "Let's achieve your goals together! 💪",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu command"""
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "friend"
    
    main_screen = render_main_menu(chat_id, user_name)
    await update.message.reply_text(main_screen, parse_mode='Markdown')
    await update.message.reply_text(
        "📱 **Quick Commands:**\n\n"
        "**Goals:**\n"
        "🎯 /goals - View all goals\n"
        "➕ /addgoal - Add new goal\n"
        "📊 /goalinfo <id> - Goal details\n"
        "✅ /goaldone <id> - Mark done\n\n"
        "**Habits:**\n"
        "🔄 /habits - View all habits\n"
        "➕ /addhabit - Add new habit\n"
        "📊 /habitinfo <id> - Habit details\n"
        "✅ /habitdone <id> - Mark done\n\n"
        "**Other:**\n"
        "💪 /boost - Get motivation\n"
        "❓ /help - Get help\n\n"
        "Or use the buttons below! 👇",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive help message"""
    help_text = """
🤖 **SoulFriend - Your AI Accountability Partner**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 Goals Management:**

/goals - View all your active goals
/addgoal - Create a new goal with target days
/goalinfo <id> - View detailed goal info
  Example: `/goalinfo 1`
/goaldone <id> - Mark goal as done today
  Example: `/goaldone 1`

**🔄 Habits Management:**

/habits - View all your active habits
/addhabit - Start a new 21-day habit challenge
/habitinfo <id> - View detailed habit info
  Example: `/habitinfo 1`
/habitdone <id> - Mark habit as completed today
  Example: `/habitdone 1`

**📊 Progress & Motivation:**

/menu - Show main menu with overview
/boost - Get AI-powered motivation
📊 My Progress button - View detailed stats

**⚙️ Other Commands:**

/help - Show this help message
/cancel - Cancel current conversation
/start - Restart and see welcome screen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**💡 Pro Tips:**

• Use the menu buttons for quick access
• Each goal/habit has a unique ID number
• You'll get reminders 3x daily at 9 AM, 2 PM, 8 PM
• AI provides personalized motivation based on your progress
• Build habits in 21 days - science-backed timeline!

**🆘 Need Help?**

Just type your question naturally, and I'll help you out!

Let's crush your goals together! 💪
"""
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def boost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get instant motivation boost"""
    chat_id = update.effective_chat.id
    from services.storage_service import get_all_goals, get_all_habits
    
    goals_list = get_all_goals(chat_id)
    habits_list = get_all_habits(chat_id)
    
    if not goals_list and not habits_list:
        await update.message.reply_text(
            "💪 **You haven't set any goals or habits yet!**\n\n"
            "Let's get started:\n"
            "• /addgoal - Set your first goal\n"
            "• /addhabit - Start a 21-day habit challenge\n\n"
            "The journey of a thousand miles begins with a single step! 🚀",
            parse_mode='Markdown'
        )
        return
    
    goals_text = ", ".join([g['goal'] for g in goals_list]) if goals_list else "my goals"
    habits_text = ", ".join([h['habit'] for h in habits_list]) if habits_list else "building habits"
    
    prompt = f"Give me a powerful motivational boost! I'm working on these goals: {goals_text}. And building these habits: {habits_text}. Be energetic, specific, and inspiring! Keep it under 100 words."
    ai_msg = chat_with_ai(prompt, chat_id)
    
    await update.message.reply_text(
        f"💪 **Your Daily Boost**\n\n{ai_msg}\n\n"
        f"🔥 You've got this! Keep pushing forward! 🚀",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
