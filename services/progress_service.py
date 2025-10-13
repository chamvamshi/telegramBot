"""
Progress Display Service - FREE USERS ONLY
No weekly charts/reports - Premium only
"""

from database import get_all_goals, get_all_habits, get_user
from database.premium_db import is_premium_user
from datetime import date
from services.limit_checker import get_remaining_limits

def render_progress_screen(chat_id):
    """Render simple progress screen - today only"""
    is_premium = is_premium_user(chat_id)
    
    # Get data
    goals = get_all_goals(chat_id, status='active')
    habits = get_all_habits(chat_id, status='active')
    
    # Get limits
    limits = get_remaining_limits(chat_id)
    
    # Count completed today - check goals/habits tables directly
    from database.connection import get_db_connection
    connection = get_db_connection()
    
    goals_completed_today = 0
    habits_completed_today = 0
    mood_status = "Not checked today"
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            today = date.today()
            
            # Count goals marked done today
            cursor.execute("""
                SELECT COUNT(*) as count FROM goals
                WHERE chat_id = %s AND status = 'completed' 
                AND DATE(completed_at) = %s
            """, (chat_id, today))
            result = cursor.fetchone()
            if result:
                goals_completed_today = result['count']
            
            # Count habits marked done today
            cursor.execute("""
                SELECT COUNT(*) as count FROM habits
                WHERE chat_id = %s AND status = 'completed'
                AND DATE(completed_at) = %s
            """, (chat_id, today))
            result = cursor.fetchone()
            if result:
                habits_completed_today = result['count']
            
            # Mood check today
            cursor.execute("""
                SELECT mood FROM mood_tracking 
                WHERE chat_id = %s AND track_date = %s 
                ORDER BY created_at DESC LIMIT 1
            """, (chat_id, today))
            mood_result = cursor.fetchone()
            if mood_result:
                mood_map = {
                    'great': '😊 Great',
                    'good': '🙂 Good',
                    'okay': '😐 Okay',
                    'stressed': '😰 Stressed',
                    'lonely': '😔 Lonely',
                    'anxious': '😟 Anxious'
                }
                mood_status = mood_map.get(mood_result['mood'], mood_result['mood'])
                
        except Exception as e:
            print(f"Progress screen error: {e}")
        finally:
            cursor.close()
            connection.close()
    
    # Build message
    plan = "💎 Premium" if is_premium else "🆓 Free Plan"
    
    message = f"📊 **Your Progress Today**\n\n"
    message += f"{plan}\n\n"
    
    # Goals section
    message += f"🎯 **GOALS** ({limits['goals']})\n"
    if goals:
        for g in goals[:5]:
            status = "✅" if g.get('status') == 'completed' else "⏳"
            message += f"  {status} {g['goal']}\n"
    else:
        message += "  No active goals yet\n"
    
    if goals_completed_today > 0:
        message += f"  \n🎉 Completed today: {goals_completed_today}\n"
    message += "\n"
    
    # Habits section
    message += f"🔄 **HABITS** ({limits['habits']})\n"
    if habits:
        for h in habits[:5]:
            status = "✅" if h.get('status') == 'completed' else "⏳"
            message += f"  {status} {h['habit']}\n"
    else:
        message += "  No active habits yet\n"
    
    if habits_completed_today > 0:
        message += f"  \n🔥 Completed today: {habits_completed_today}\n"
    message += "\n"
    
    # Mood section
    message += f"💭 **MOOD TODAY** ({limits['mood_checks']})\n"
    message += f"  {mood_status}\n\n"
    
    # FREE vs PREMIUM messaging
    if not is_premium:
        message += "---\n"
        message += "🔒 **Unlock Premium Features:**\n"
        message += "• 📈 Weekly visual charts & graphs\n"
        message += "• 🧠 AI psychology insights\n"
        message += "• 📊 Detailed behavior reports\n"
        message += "• ♾️ Unlimited goals, habits, mood checks\n"
        message += "• 🎯 Advanced goal tracking\n\n"
        message += "💎 Tap /premium to upgrade!"
    else:
        # Premium users get access to reports
        message += "---\n"
        message += "💎 **Premium Features:**\n"
        message += "📈 \n"
        message += "📊 \n"
        message += "🧠 "
    
    return message
