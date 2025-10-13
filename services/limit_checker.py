from database import get_all_goals, get_all_habits, get_user
from database.premium_db import is_premium_user
from datetime import datetime


def can_add_goal(chat_id):
    """Check if user can add more goals (Free: 3 max, Premium: unlimited)"""
    # Premium users have unlimited
    if is_premium_user(chat_id):
        return True, None
    
    # Free users: check limit
    active_goals = get_all_goals(chat_id, status='active')
    
    if len(active_goals) >= 3:
        return False, (
            "🔒 **Free Plan Limit: 3 Goals Max**\n\n"
            "You're doing great! But you've hit your limit.\n\n"
            
            "💡 **Quick Fix:**\n"
            "Complete or archive a goal to add new ones.\n\n"
            
            "🚀 **Or Go Unlimited:**\n"
            "Premium users can add UNLIMITED goals + get:\n"
            "• 📊 Weekly progress charts\n"
            "• 🧠 AI insights on what's working\n"
            "• 🎯 Smart goal recommendations\n\n"
            
            "💎 Just ₹99/month (~3 coffees ☕)\n"
            "Try FREE for 7 days → /activatedemo\n\n"
            "Learn more: /premium"
        )
    
    return True, None


def can_add_habit(chat_id):
    """Check if user can add more habits (Free: 3 max, Premium: unlimited)"""
    # Premium users have unlimited
    if is_premium_user(chat_id):
        return True, None
    
    # Free users: check limit
    active_habits = get_all_habits(chat_id, status='active')
    
    if len(active_habits) >= 3:
        return False, (
            "🔒 **Free Plan Limit: 3 Habits Max**\n\n"
            "Building habits is powerful, but you're maxed out!\n\n"
            
            "💡 **Options:**\n"
            "1. Complete/archive an old habit\n"
            "2. Upgrade to Premium for UNLIMITED habits\n\n"
            
            "🚀 **Premium Perks:**\n"
            "• ♾️ Unlimited habits & goals\n"
            "• 🔥 Visual streak tracking\n"
            "• 📈 Weekly behavior analysis\n"
            "• 🧠 AI-powered habit coaching\n\n"
            
            "💎 Only ₹99/month - Try FREE for 7 days!\n"
            "Tap /activatedemo now 👉"
        )
    
    return True, None


def can_check_mood(chat_id):
    """Check if user can check mood (Free: 2/day, Premium: unlimited)"""
    # Premium users have unlimited
    if is_premium_user(chat_id):
        return True, None
    
    # Free users: check daily limit
    user = get_user(chat_id)
    
    if not user:
        return True, None  # New user, allow
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_check = user.get('last_mood_check', '')
    mood_count = user.get('mood_checks_today', 0)
    
    # Reset counter if new day
    if last_check != today:
        return True, None
    
    # Check if limit reached
    if mood_count >= 2:
        return False, (
            "🔒 **Free Plan: 2 Mood Checks/Day**\n\n"
            "You've reached your daily limit. Come back tomorrow! 🌅\n\n"
            
            "😔 **Need More Support?**\n"
            "Premium gives you UNLIMITED mood check-ins plus:\n"
            "• 🧠 Psychology insights from your patterns\n"
            "• 📊 Weekly emotional analysis\n"
            "• 💬 Deeper AI conversations anytime\n"
            "• 🎯 Personalized coping strategies\n\n"
            
            "💎 **Just ₹99/month** - Less than a movie ticket! 🎬\n"
            "Try all features FREE for 7 days!\n\n"
            "Tap /activatedemo to start your trial!"
        )
    
    return True, None
def can_view_progress(chat_id):
    """Check if user can view progress (Free: basic text, Premium: charts + AI insights)"""
    if is_premium_user(chat_id):
        return True, None
    
    return False, (
        "🔒 **Free Plan: Basic Progress Only**\n\n"
        "You can view simple text summaries of your progress.\n\n"
        
        "🚀 **Upgrade to Premium for Full Insights:**\n"
        "• 📊 Visual progress charts & streaks\n"
        "• 🧠 AI-driven behavior analysis\n"
        "• 🎯 Smart recommendations to improve\n"
        "• 🏆 Achievement badges & milestones\n\n"
        
        "💎 All this for just ₹99/month (~3 coffees ☕)\n"
        "Try FREE for 7 days → /activatedemo\n\n"
        "Learn more: /premium"
    )
    
    

def increment_mood_check(chat_id):
    """Increment mood check counter for free users"""
    from database import get_db_connection
    from datetime import datetime
    
    # Premium users don't need tracking
    if is_premium_user(chat_id):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Get current user data
        cursor.execute('SELECT last_mood_check, mood_checks_today FROM users WHERE chat_id = %s', (chat_id,))
        result = cursor.fetchone()
        
        if result:
            last_check, mood_count = result
            
            # Reset counter if new day
            if last_check != today:
                mood_count = 0
            
            # Increment
            mood_count += 1
            
            # Update database
            cursor.execute('''
                UPDATE users 
                SET last_mood_check = %s, mood_checks_today = %s
                WHERE chat_id = %s
            ''', (today, mood_count, chat_id))
            conn.commit()
    finally:
        conn.close()



def get_remaining_limits(chat_id):
    """Get remaining limits for free users"""
    from database.premium_db import is_premium_user
    from database import get_all_goals, get_all_habits, get_user
    from datetime import datetime
    
    # Premium users have no limits
    if is_premium_user(chat_id):
        return {
            'goals': {'used': 0, 'limit': 'Unlimited', 'remaining': 'Unlimited'},
            'habits': {'used': 0, 'limit': 'Unlimited', 'remaining': 'Unlimited'},
            'mood_checks': {'used': 0, 'limit': 'Unlimited', 'remaining': 'Unlimited'}
        }
    
    # Free user - calculate limits
    active_goals = get_all_goals(chat_id, status='active')
    active_habits = get_all_habits(chat_id, status='active')
    
    user = get_user(chat_id)
    today = datetime.now().strftime('%Y-%m-%d')
    last_check = user.get('last_mood_check', '') if user else ''
    mood_count = user.get('mood_checks_today', 0) if user else 0
    
    # Reset mood count if new day
    if last_check != today:
        mood_count = 0
    
    return {
        'goals': {
            'used': len(active_goals),
            'limit': 3,
            'remaining': max(0, 3 - len(active_goals))
        },
        'habits': {
            'used': len(active_habits),
            'limit': 3,
            'remaining': max(0, 3 - len(active_habits))
        },
        'mood_checks': {
            'used': mood_count,
            'limit': 2,
            'remaining': max(0, 2 - mood_count),
            'resets': 'daily'
        }
    }
