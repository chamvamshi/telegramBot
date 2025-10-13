"""
Mood & Conversation Tracking Database Operations
"""
from .connection import get_db_connection
from datetime import date, timedelta
def save_mood(chat_id, mood, feeling_notes=None, energy_level=5):
    """Save user's daily mood to database"""
    connection = get_db_connection()
    if not connection:
        return False
    cursor = connection.cursor(buffered=True)
    try:
        today = date.today()
        cursor.execute("""
            INSERT INTO mood_tracking (chat_id, track_date, mood, feeling_notes, energy_level)
            VALUES (%s, %s, %s, %s, %s)
        """, (chat_id, today, mood, feeling_notes, energy_level))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()
def get_weekly_moods(chat_id):
    """Get user's moods from last 7 days"""
    connection = get_db_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True, buffered=True)
    try:
        seven_days_ago = date.today() - timedelta(days=7)
        cursor.execute("""
            SELECT track_date, mood, feeling_notes, energy_level
            FROM mood_tracking WHERE chat_id = %s AND track_date >= %s ORDER BY track_date DESC
        """, (chat_id, seven_days_ago))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
def save_conversation(chat_id, message, context='general'):
    """Save conversation message (allows multiple per day)"""
    connection = get_db_connection()
    if not connection:
        return False
    cursor = connection.cursor(buffered=True)
    try:
        from datetime import datetime
        today = date.today()
        now = datetime.now()
        
        # Save with timestamp to allow multiple messages per day
        cursor.execute("""
            INSERT INTO conversation_history 
            (chat_id, message_date, user_message, context, message_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (chat_id, today, message[:500] if message else "", context, now))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False
    finally:
        cursor.close()
        connection.close()
def get_weekly_conversations(chat_id):
    """Get conversations from last 7 days"""
    connection = get_db_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True, buffered=True)
    try:
        seven_days_ago = date.today() - timedelta(days=7)
        cursor.execute("""
            SELECT message_date, user_message, context
            FROM conversation_history WHERE chat_id = %s AND message_date >= %s
            ORDER BY message_date DESC LIMIT 20
        """, (chat_id, seven_days_ago))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
