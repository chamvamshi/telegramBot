"""
Habit Database Operations
All functions related to habits
"""

from .connection import get_db_connection
import json
from datetime import date

def add_habit(chat_id, habit_text, reminder_times=None):
    """Add new habit"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor()
    try:
        # Get next habit_id for this user
        cursor.execute(
            "SELECT COALESCE(MAX(habit_id), 0) + 1 FROM habits WHERE chat_id = %s",
            (chat_id,)
        )
        habit_id = cursor.fetchone()[0]
        
        # Insert new habit
        cursor.execute("""
            INSERT INTO habits (chat_id, habit_id, habit, start_date, reminder_times)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            chat_id,
            habit_id,
            habit_text,
            date.today(),
            json.dumps(reminder_times or ["09:00"])
        ))
        
        connection.commit()
        return habit_id
        
    finally:
        cursor.close()
        connection.close()


def get_all_habits(chat_id, status='active'):
    """Get all habits for user by status"""
    connection = get_db_connection()
    if not connection:
        return []
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT habit_id as id, habit, days_target, streak, start_date,
                   reminder_times, last_completed, status, completed_date
            FROM habits 
            WHERE chat_id = %s AND status = %s 
            ORDER BY habit_id
        """, (chat_id, status))
        
        habits = cursor.fetchall()
        
        # Parse JSON and convert dates to strings
        for habit in habits:
            if habit['reminder_times']:
                habit['reminder_times'] = json.loads(habit['reminder_times'])
            
            # Convert dates to ISO format strings
            for field in ['start_date', 'last_completed', 'completed_date']:
                if habit[field]:
                    habit[field] = habit[field].isoformat()
        
        return habits
        
    finally:
        cursor.close()
        connection.close()


def get_habit_by_id(chat_id, habit_id):
    """Get specific habit by ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT habit_id as id, habit, days_target, streak, start_date,
                   reminder_times, last_completed, status, completed_date
            FROM habits 
            WHERE chat_id = %s AND habit_id = %s
        """, (chat_id, habit_id))
        
        habit = cursor.fetchone()
        
        if habit:
            if habit['reminder_times']:
                habit['reminder_times'] = json.loads(habit['reminder_times'])
            
            # Convert dates to ISO format strings
            for field in ['start_date', 'last_completed', 'completed_date']:
                if habit[field]:
                    habit[field] = habit[field].isoformat()
        
        return habit
        
    finally:
        cursor.close()
        connection.close()


def complete_habit_today(chat_id, habit_id):
    """Mark habit as done for today"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection error"
    
    cursor = connection.cursor(dictionary=True)
    try:
        today = date.today()
        
        # Get current habit
        cursor.execute("""
            SELECT habit_id as id, habit, streak, last_completed
            FROM habits 
            WHERE chat_id = %s AND habit_id = %s
        """, (chat_id, habit_id))
        
        habit = cursor.fetchone()
        
        if not habit:
            return False, "Habit not found!"
        
        # Check if already completed today
        if habit['last_completed'] and habit['last_completed'] == today:
            return False, "Already completed today! ✅"
        
        # Increment streak
        new_streak = habit['streak'] + 1
        
        # Check if 21-day challenge is complete
        if new_streak >= 21:
            cursor.execute("""
                UPDATE habits 
                SET streak = %s, last_completed = %s, status = 'completed', completed_date = %s
                WHERE chat_id = %s AND habit_id = %s
            """, (new_streak, today, today, chat_id, habit_id))
            connection.commit()
            
            return True, (
                f"🎉🎉🎉 **21-DAY CHALLENGE COMPLETE!** 🎉🎉🎉\n\n"
                f"You've mastered: **{habit['habit']}**\n\n"
                f"🏆 This habit is now part of who you are!\n"
                f"🔥 Final streak: 21 days\n\n"
                f"View all achievements: /completedhabits"
            )
        else:
            # Just update streak
            cursor.execute("""
                UPDATE habits 
                SET streak = %s, last_completed = %s
                WHERE chat_id = %s AND habit_id = %s
            """, (new_streak, today, chat_id, habit_id))
            connection.commit()
            
            days_left = 21 - new_streak
            return True, f"Awesome! {new_streak} day streak on '{habit['habit']}'! 💪\n\n{days_left} days to go!"
        
    finally:
        cursor.close()
        connection.close()


def update_habit_name(chat_id, habit_id, new_name):
    """Update habit name"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE habits 
            SET habit = %s 
            WHERE chat_id = %s AND habit_id = %s
        """, (new_name, chat_id, habit_id))
        
        connection.commit()
        return cursor.rowcount > 0
        
    finally:
        cursor.close()
        connection.close()


def update_habit_streak(chat_id, habit_id, new_streak):
    """Update habit streak and adjust status"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        if new_streak >= 21:
            # Mark as completed if streak reaches 21
            cursor.execute("""
                UPDATE habits 
                SET streak = %s, status = 'completed',
                    completed_date = COALESCE(completed_date, CURRENT_DATE)
                WHERE chat_id = %s AND habit_id = %s
            """, (new_streak, chat_id, habit_id))
        else:
            # Keep active and clear completed date
            cursor.execute("""
                UPDATE habits 
                SET streak = %s, status = 'active', completed_date = NULL
                WHERE chat_id = %s AND habit_id = %s
            """, (new_streak, chat_id, habit_id))
        
        connection.commit()
        return cursor.rowcount > 0
        
    finally:
        cursor.close()
        connection.close()


def update_habit_reminders(chat_id, habit_id, reminder_times):
    """Update habit reminder times"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE habits 
            SET reminder_times = %s 
            WHERE chat_id = %s AND habit_id = %s
        """, (json.dumps(reminder_times), chat_id, habit_id))
        
        connection.commit()
        return cursor.rowcount > 0
        
    finally:
        cursor.close()
        connection.close()


def delete_habit(chat_id, habit_id):
    """Delete a habit"""
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            DELETE FROM habits 
            WHERE chat_id = %s AND habit_id = %s
        """, (chat_id, habit_id))
        
        connection.commit()
        
    finally:
        cursor.close()
        connection.close()


def mark_habit_complete(chat_id, habit_id):
    """Manually mark habit as completed"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection error"
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Get habit name
        cursor.execute("""
            SELECT habit 
            FROM habits 
            WHERE chat_id = %s AND habit_id = %s
        """, (chat_id, habit_id))
        
        habit = cursor.fetchone()
        if not habit:
            return False, "Habit not found!"
        
        # Mark as completed
        cursor.execute("""
            UPDATE habits 
            SET status = 'completed', 
                completed_date = COALESCE(completed_date, CURRENT_DATE)
            WHERE chat_id = %s AND habit_id = %s
        """, (chat_id, habit_id))
        
        connection.commit()
        return True, f"🎉 Habit mastered: {habit['habit']}"
        
    finally:
        cursor.close()
        connection.close()
