"""
Start & Menu Handlers with Persistent Navigation
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_user
from services.ui_service import (
    get_main_menu_keyboard, 
    get_goals_menu_keyboard,
    get_habits_menu_keyboard,
    get_settings_menu_keyboard,
    render_main_menu
)
from services.ai_response import chat_with_ai

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show main menu"""
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    
    if not user or not user.get('onboarded'):
        await update.message.reply_text(
            "👋 Welcome to SoulFriend!\n\n"
            "Let me help you build better habits and achieve your goals!\n\n"
            "Let's get started with quick setup..."
        )
        return
    
    user_name = user.get('name', 'friend')
    
    await update.message.reply_text(
        render_main_menu(user_name),
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    user_name = user.get('name', 'friend') if user else 'friend'
    
    await update.message.reply_text(
        render_main_menu(user_name),
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_goals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show goals submenu"""
    await update.message.reply_text(
        "🎯 **Goal Management**\n\nWhat would you like to do?",
        reply_markup=get_goals_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_habits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show habits submenu"""
    await update.message.reply_text(
        "🔄 **Habit Management**\n\nWhat would you like to do?",
        reply_markup=get_habits_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    await update.message.reply_text(
        "⚙️ **Settings**\n\nManage your preferences:",
        reply_markup=get_settings_menu_keyboard(),
        parse_mode='Markdown'
    )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    await menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        "ℹ️ **How to Use SoulFriend**\n\n"
        "Use the buttons below to navigate!\n\n"
        "**Quick Commands:**\n"
        "🎯 Goals - Track your objectives\n"
        "🔄 Habits - Build routines\n"
        "💭 Mood - Emotional check-in\n"
        "📊 Reports - View progress\n\n"
        "_Tap any button to start!_",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def boost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get AI motivation"""
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    user_name = user.get('name', 'friend') if user else 'friend'
    
    prompt = f"Give {user_name} a powerful, motivational message to boost their day. Be energetic and inspiring. 2-3 sentences."
    motivation = chat_with_ai(prompt, chat_id)
    
    await update.message.reply_text(
        f"💪 **Daily Boost**\n\n{motivation}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text("Profile not found. Use /start")
        return
    
    from database import get_all_goals, get_all_habits
    goals = get_all_goals(chat_id, status='active')
    habits = get_all_habits(chat_id, status='active')
    
    profile_text = f"""👤 **Your Profile**

**Name:** {user.get('name', 'N/A')}
**Country:** {user.get('country', 'N/A')}
**Timezone:** {user.get('timezone', 'UTC')}
**EOD Time:** {user.get('eod_time', 'Not set')}

**Active:**
🎯 {len(goals)} Goals
🔄 {len(habits)} Habits

Keep going! 💪"""
    
    await update.message.reply_text(
        profile_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
