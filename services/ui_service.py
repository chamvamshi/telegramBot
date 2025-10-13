"""
Simple, User-Friendly Menu System
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Clean main menu - only essentials"""
    keyboard = [
        [KeyboardButton("🎯 Goals"), KeyboardButton("🔄 Habits")],
        [KeyboardButton("💭 Check Mood"), KeyboardButton("📊 My Progress")],
        [KeyboardButton("💪 Get Motivated"), KeyboardButton("⚙️ Settings")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_goals_menu_keyboard():
    """Simple goals menu"""
    keyboard = [
        [KeyboardButton("➕ Add New Goal")],
        [KeyboardButton("📋 View My Goals")],
        [KeyboardButton("✅ Mark Goal Done")],
        [KeyboardButton("🔙 Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_habits_menu_keyboard():
    """Simple habits menu"""
    keyboard = [
        [KeyboardButton("➕ Add New Habit")],
        [KeyboardButton("📋 View My Habits")],
        [KeyboardButton("✅ Mark Habit Done")],
        [KeyboardButton("🔙 Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_menu_keyboard():
    """Simple settings menu"""
    keyboard = [
        [KeyboardButton("⏰ Set Daily Summary Time")],
        [KeyboardButton("🌍 Change Timezone")],
        [KeyboardButton("👤 My Profile")],
        [KeyboardButton("💎 Premium Features")],
        [KeyboardButton("🔙 Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def render_main_menu(user_name):
    """Simple, clear main menu text"""
    return f"""👋 **Hey {user_name}!**

**Choose what you want to do:**

🎯 **Goals** - Add & track your goals
🔄 **Habits** - Build daily habits
💭 **Check Mood** - Talk about your feelings
📊 **My Progress** - See weekly stats & badges
💪 **Get Motivated** - AI boost message
⚙️ **Settings** - Manage preferences

_Just tap a button below!_ 👇"""
