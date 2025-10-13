"""
User Database Operations
All functions related to users
"""

from .connection import get_db_connection
import json

def get_user(chat_id):
    """Get user by chat_id"""
    connection = get_db_connection()
    if not connection:
        return {'chat_id': chat_id, 'timezone': 'UTC', 'onboarded': False}
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute("INSERT INTO users (chat_id) VALUES (%s)", (chat_id,))
            connection.commit()
            return {
                'chat_id': chat_id,
                'name': None,
                'country': None,
                'timezone': 'UTC',
                'onboarded': False,
                'eod_time': None
            }
        
        return user
        
    finally:
        cursor.close()
        connection.close()


def save_user(chat_id, user_data):
    """Save or update user"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (chat_id, name, country, timezone, onboarded, eod_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name), 
                country = VALUES(country),
                timezone = VALUES(timezone), 
                onboarded = VALUES(onboarded), 
                eod_time = VALUES(eod_time)
        """, (
            chat_id,
            user_data.get('name'),
            user_data.get('country'),
            user_data.get('timezone', 'UTC'),
            user_data.get('onboarded', False),
            user_data.get('eod_time')
        ))
        
        connection.commit()
        return True
        
    finally:
        cursor.close()
        connection.close()


def get_user_profile(chat_id):
    """Get user profile"""
    user = get_user(chat_id)
    return {
        'name': user.get('name'),
        'country': user.get('country'),
        'timezone': user.get('timezone', 'UTC'),
        'onboarded': user.get('onboarded', False)
    }


def set_user_profile(chat_id, name, country, timezone):
    """Set user profile"""
    return save_user(chat_id, {
        'name': name,
        'country': country,
        'timezone': timezone,
        'onboarded': True
    })


def is_user_onboarded(chat_id):
    """Check if user completed onboarding"""
    user = get_user(chat_id)
    return user.get('onboarded', False)


def get_user_timezone(chat_id):
    """Get user timezone"""
    user = get_user(chat_id)
    return user.get('timezone', 'UTC')


def set_user_timezone(chat_id, timezone_name):
    """Set user timezone"""
    user = get_user(chat_id)
    user['timezone'] = timezone_name
    return save_user(chat_id, user)


def load_data():
    """Load all user data for reminder scheduling"""
    connection = get_db_connection()
    if not connection:
        return {}
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        data = {}
        for user in users:
            chat_id = str(user['chat_id'])
            
            # Get goals
            cursor.execute("""
                SELECT goal_id as id, goal, target_days, streak, start_date, motivation,
                       last_checkin, status, reminder_times, completed_date
                FROM goals WHERE chat_id = %s
            """, (user['chat_id'],))
            goals = cursor.fetchall()
            
            # Parse JSON and dates for goals
            for goal in goals:
                if goal['reminder_times']:
                    goal['reminder_times'] = json.loads(goal['reminder_times'])
                for field in ['start_date', 'last_checkin', 'completed_date']:
                    if goal[field]:
                        goal[field] = goal[field].isoformat()
            
            # Get habits
            cursor.execute("""
                SELECT habit_id as id, habit, days_target, streak, start_date,
                       reminder_times, last_completed, status, completed_date
                FROM habits WHERE chat_id = %s
            """, (user['chat_id'],))
            habits = cursor.fetchall()
            
            # Parse JSON and dates for habits
            for habit in habits:
                if habit['reminder_times']:
                    habit['reminder_times'] = json.loads(habit['reminder_times'])
                for field in ['start_date', 'last_completed', 'completed_date']:
                    if habit[field]:
                        habit[field] = habit[field].isoformat()
            
            data[chat_id] = {
                'name': user['name'],
                'country': user['country'],
                'timezone': user['timezone'],
                'onboarded': user['onboarded'],
                'eod_time': user['eod_time'],
                'goals': goals,
                'habits': habits
            }
        
        return data
        
    finally:
        cursor.close()
        connection.close()
