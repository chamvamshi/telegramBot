"""
Premium & Analytics Database Operations
"""

from .connection import get_db_connection
from datetime import date, timedelta

def is_premium_user(chat_id):
    """Check if user has active premium subscription"""
    connection = get_db_connection()
    if not connection:
        return False
    cursor = connection.cursor(dictionary=True, buffered=True)  # 🔥 Added buffered=True
    try:
        cursor.execute("""
            SELECT * FROM premium_users 
            WHERE chat_id = %s AND is_active = TRUE AND end_date >= CURRENT_DATE
        """, (chat_id,))
        result = cursor.fetchone()
        return result is not None
    finally:
        cursor.close()
        connection.close()

def activate_premium(chat_id, subscription_type='monthly', payment_id=None):
    """Activate premium subscription"""
    connection = get_db_connection()
    if not connection:
        return False
    cursor = connection.cursor(buffered=True)  # 🔥 Added buffered=True
    try:
        start = date.today()
        if subscription_type == 'monthly':
            end = start + timedelta(days=30)
        else:
            end = start + timedelta(days=365)
        cursor.execute("""
            INSERT INTO premium_users (chat_id, subscription_type, start_date, end_date, payment_id)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE end_date = VALUES(end_date), is_active = TRUE
        """, (chat_id, subscription_type, start, end, payment_id))
        connection.commit()
        return True
    finally:
        cursor.close()
        connection.close()

def track_daily_progress(chat_id):
    """Track daily progress"""
    from .goal_db import get_all_goals
    from .habit_db import get_all_habits
    connection = get_db_connection()
    if not connection:
        return
    cursor = connection.cursor(buffered=True)  # 🔥 Added buffered=True
    try:
        today = date.today()
        goals = get_all_goals(chat_id, status='active')
        habits = get_all_habits(chat_id, status='active')
        goals_completed = sum(1 for g in goals if g.get('last_checkin') == today.isoformat())
        habits_completed = sum(1 for h in habits if h.get('last_completed') == today.isoformat())
        cursor.execute("""
            INSERT INTO daily_tracking (chat_id, track_date, goals_completed, habits_completed, total_goals, total_habits)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE goals_completed = VALUES(goals_completed), habits_completed = VALUES(habits_completed), total_goals = VALUES(total_goals), total_habits = VALUES(total_habits)
        """, (chat_id, today, goals_completed, habits_completed, len(goals), len(habits)))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def get_weekly_stats(chat_id, week_offset=0):
    """Get weekly statistics"""
    connection = get_db_connection()
    if not connection:
        return None
    cursor = connection.cursor(dictionary=True, buffered=True)  # 🔥 Added buffered=True
    try:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday() + (week_offset * 7))
        end_of_week = start_of_week + timedelta(days=6)
        cursor.execute("""
            SELECT SUM(goals_completed) as goals_completed, SUM(habits_completed) as habits_completed,
                   SUM(total_goals) as total_goals, SUM(total_habits) as total_habits
            FROM daily_tracking WHERE chat_id = %s AND track_date BETWEEN %s AND %s
        """, (chat_id, start_of_week, end_of_week))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        connection.close()

def award_badge(chat_id, badge_type, completion_rate):
    """Award badge to user"""
    connection = get_db_connection()
    if not connection:
        return False
    cursor = connection.cursor(buffered=True)  # 🔥 Added buffered=True
    try:
        today = date.today()
        week_num = today.isocalendar()[1]
        year = today.year
        badge_names = {'soul_silver': '🥈 Soul Silver', 'soul_gold': '🥇 Soul Gold', 'soul_diamond': '💎 Soul Diamond', 'pure_soul': '👑 Pure Soul'}
        cursor.execute("""
            INSERT INTO achievements (chat_id, badge_type, badge_name, earned_date, week_number, year, completion_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE completion_rate = VALUES(completion_rate)
        """, (chat_id, badge_type, badge_names.get(badge_type), today, week_num, year, completion_rate))
        connection.commit()
        return True
    finally:
        cursor.close()
        connection.close()

def get_user_badges(chat_id):
    """Get all user badges"""
    connection = get_db_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True, buffered=True)  # 🔥 Added buffered=True
    try:
        cursor.execute("SELECT * FROM achievements WHERE chat_id = %s ORDER BY earned_date DESC", (chat_id,))
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()
        connection.close()


def activate_demo_trial(chat_id):
    """Activate 7-day free premium trial for user"""
    from datetime import datetime, timedelta
    
    connection = get_db_connection()
    if not connection:
        return False, "❌ Database connection failed. Please try again."
    
    cursor = connection.cursor(dictionary=True, buffered=True)
    
    try:
        # Check if user already used trial
        cursor.execute("""
            SELECT * FROM premium_users 
            WHERE chat_id = %s
        """, (chat_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Check if already active
            if existing.get('is_active'):
                return False, (
                    "💎 **You're Already Premium!**\n\n"
                    "You're currently enjoying premium features.\n\n"
                    "Keep tracking your goals and building habits! 🚀"
                )
            else:
                # Previously used trial
                return False, (
                    "⚠️ **Trial Already Used**\n\n"
                    "You've already used your free trial.\n\n"
                    "💰 Upgrade to premium:\n"
                    "• ₹99/month\n"
                    "• ₹999/year\n\n"
                    "Payment coming soon! 🎉"
                )
        
        # Activate trial
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        cursor.execute("""
            INSERT INTO premium_users 
            (chat_id, subscription_type, is_active, start_date, end_date)
            VALUES (%s, %s, TRUE, %s, %s)
        """, (chat_id, 'trial', start_date, end_date))
        
        connection.commit()
        
        return True, (
            "🎉 **Free Trial Activated!**\n\n"
            "Welcome to Premium for 7 days!\n\n"
            "✅ **Unlocked Features:**\n"
            "• ♾️ Unlimited goals & habits\n"
            "• �� Unlimited mood check-ins\n"
            "• 📊 Full progress tracking\n\n"
            "🎁 **Coming in v2.0:** AI insights, badges, analytics\n\n"
            f"📅 Trial ends: {end_date.strftime('%B %d, %Y')}\n\n"
            "🚀 Start creating unlimited goals and habits now!"
        )
    
    except Exception as e:
        print(f"Error activating demo trial: {e}")
        return False, "❌ Error activating trial. Please try again."
    
    finally:
        cursor.close()
        connection.close()
