# UI Configuration - Change designs here without touching main code
UI_CONFIG = {
    "emojis": {
        "goals": "🎯",
        "habits": "🔄", 
        "support": "💙",
        "stats": "📊",
        "boost": "✨",
        "fire": "🔥",
        "check": "✅",
        "star": "🌟",
        "wave": "👋",
        "trophy": "🏆"
    },
    "colors": {
        "success": "🟢",
        "warning": "🟡", 
        "danger": "🔴",
        "progress_full": "█",
        "progress_empty": "░"
    },
    "messages": {
        "welcome_title": "🌟 SoulFriend - Your AI\n     Accountability Partner",
        "ready_message": "Ready to crush your goals?",
        "progress_title": "📊 Today's Progress:"
    }
}

def get_progress_bar(current, total, length=10):
    """Generate visual progress bar"""
    filled = int((current / total) * length)
    return "█" * filled + "░" * (length - filled)

def get_calendar_view(streak_data):
    """Generate weekly calendar view"""
    days = ["S", "M", "T", "W", "T", "F", "S"]
    symbols = []
    for i, day in enumerate(streak_data):
        if day == 1:
            symbols.append("✅")
        elif day == 0:
            symbols.append("❌") 
        else:
            symbols.append("?")
    
    calendar = "  ".join(days) + "\n"
    calendar += "  ".join(symbols)
    return calendar
