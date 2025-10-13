"""
Menu Button Handlers - Complete & Working
"""

from telegram import Update
from telegram.ext import ContextTypes

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # DEBUG: Print button text
    if update.message and update.message.text:
        button_text = update.message.text
        print(f"🔍 BUTTON CLICKED: '{button_text}'")
        print(f"🔍 BUTTON BYTES: {button_text.encode('utf-8')}")
    """Handle all button clicks"""
    text = update.message.text
    
    from handlers import start, goals, habits
    from services.ui_service import get_main_menu_keyboard
    
    # ========== MAIN MENU ==========
    
    if text == "🎯 Goals":
        await show_goals_menu(update, context)
    
    elif text == "�� Habits":
        await show_habits_menu(update, context)

    elif text == "🔄 Habits":
        await show_habits_menu(update, context)

    
    elif text == "💭 Check Mood":
        from handlers.mood_enhanced import check_mood_command
        await check_mood_command(update, context)
    
    elif text == "📊 My Progress":
        await show_progress(update, context)
    
    elif text == "💪 Get Motivated":
        await start.boost_command(update, context)
    
    elif text == "⚙️ Settings":
        await show_settings_menu(update, context)
    
    # ========== GOALS SUBMENU ==========
    
    elif text == "➕ Add New Goal":
        from handlers.goals import add_goal_command
        await add_goal_command(update, context)
    
    elif text == "📋 View My Goals":
        await goals.goals_command(update, context)
    
    elif text == "✅ Mark Goal Done":
        from database import get_all_goals
        chat_id = update.effective_chat.id
        active_goals = get_all_goals(chat_id, status='active')
        
        if not active_goals:
            await update.message.reply_text(
                "You have no active goals!\n\nAdd one first 🎯",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            goals_list = "\n".join([f"{g['goal_id']}. {g['goal']}" for g in active_goals[:5]])
            await update.message.reply_text(
                f"**Your Goals:**\n{goals_list}\n\n"
                f"Reply: /goaldone <number>\n"
                f"Example: /goaldone 1",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
    
    # ========== HABITS SUBMENU ==========
    
    # Handled by add_habit_handler ConversationHandler
    # elif text == "➕ Add New Habit":
        from handlers.habits import add_habit_command
        await add_habit_command(update, context)
    
    elif text == "📋 View My Habits":
        await habits.habits_command(update, context)
    
    elif text == "✅ Mark Habit Done":
        from database import get_all_habits
        chat_id = update.effective_chat.id
        active_habits = get_all_habits(chat_id, status='active')
        
        if not active_habits:
            await update.message.reply_text(
                "You have no active habits!\n\nAdd one first 🔄",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            habits_list = "\n".join([f"{h['habit_id']}. {h['habit']}" for h in active_habits[:5]])
            await update.message.reply_text(
                f"**Your Habits:**\n{habits_list}\n\n"
                f"Reply: /habitdone <number>\n"
                f"Example: /habitdone 1",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
    
    # ========== SETTINGS SUBMENU ==========
    
    elif text == "⏰ Set Daily Summary Time":
        await update.message.reply_text(
            "⏰ **Set Your Daily Summary Time**\n\n"
            "When should I send your end-of-day summary?\n\n"
            "**Usage:** /seteod HH:MM\n"
            "**Example:** /seteod 21:00\n\n"
            "_This will send your daily progress at 9 PM_",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    
    elif text == "🌍 Change Timezone":
        from handlers.timezone_handler import set_timezone_command
        await set_timezone_command(update, context)
    
    elif text == "👤 My Profile":
        await start.show_profile(update, context)
    
    elif text == "💎 Premium Features":
        from handlers.premium import premium_info_command
        await premium_info_command(update, context)
    
    # ========== BACK BUTTON ==========
    
    elif text == "🔙 Main Menu":
        await start.menu(update, context)


async def show_goals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show goals submenu"""
    from services.ui_service import get_goals_menu_keyboard
    await update.message.reply_text(
        "🎯 **Goal Management**\n\n"
        "What do you want to do with your goals?",
        reply_markup=get_goals_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_habits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show habits submenu"""
    from services.ui_service import get_habits_menu_keyboard
    await update.message.reply_text(
        "🔄 **Habit Management**\n\n"
        "What do you want to do with your habits?",
        reply_markup=get_habits_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    from services.ui_service import get_settings_menu_keyboard
    await update.message.reply_text(
        "⚙️ **Settings**\n\n"
        "Manage your preferences:",
        reply_markup=get_settings_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current progress (free: simple view, premium: with charts)"""
    chat_id = update.effective_chat.id
    from services.progress_service import render_progress_screen
    from services.ui_service import get_main_menu_keyboard
    
    progress = render_progress_screen(chat_id)
    
    await update.message.reply_text(
        progress,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
