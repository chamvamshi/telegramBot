"""
Goal Database Operations
All functions related to goals
"""

from .connection import get_db_connection
import json
from datetime import date

def add_goal(chat_id, goal_text, target_days=30, motivation_line="", reminder_times=None):
    """Add new goal"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor()
    try:
        # Get next goal_id for this user
        cursor.execute(
            "SELECT COALESCE(MAX(goal_id), 0) + 1 FROM goals WHERE chat_id = %s",
            (chat_id,)
        )
        goal_id = cursor.fetchone()[0]
        
        # Insert new goal
        cursor.execute("""
            INSERT INTO goals (chat_id, goal_id, goal, target_days, start_date, motivation, reminder_times)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            chat_id,
            goal_id,
            goal_text,
            target_days,
            date.today(),
            motivation_line or f"Stay focused on: {goal_text}",
            json.dumps(reminder_times or ["09:00"])
        ))
        
        connection.commit()
        return goal_id
        
    finally:
        cursor.close()
        connection.close()


def get_all_goals(chat_id, status='active'):
    """Get all goals for user by status"""
    connection = get_db_connection()
    if not connection:
        return []
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT goal_id as id, goal, target_days, streak, start_date, motivation,
                   last_checkin, status, reminder_times, completed_date
            FROM goals 
            WHERE chat_id = %s AND status = %s 
            ORDER BY goal_id
        """, (chat_id, status))
        
        goals = cursor.fetchall()
        
        # Parse JSON and convert dates to strings
        for goal in goals:
            if goal['reminder_times']:
                goal['reminder_times'] = json.loads(goal['reminder_times'])
            
            # Convert dates to ISO format strings
            for field in ['start_date', 'last_checkin', 'completed_date']:
                if goal[field]:
                    goal[field] = goal[field].isoformat()
        
        return goals
        
    finally:
        cursor.close()
        connection.close()


def get_goal_by_id(chat_id, goal_id):
    """Get specific goal by ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT goal_id as id, goal, target_days, streak, start_date, motivation,
                   last_checkin, status, reminder_times, completed_date
            FROM goals 
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        goal = cursor.fetchone()
        
        if goal:
            if goal['reminder_times']:
                goal['reminder_times'] = json.loads(goal['reminder_times'])
            
            # Convert dates to ISO format strings
            for field in ['start_date', 'last_checkin', 'completed_date']:
                if goal[field]:
                    goal[field] = goal[field].isoformat()
        
        return goal
        
    finally:
        cursor.close()
        connection.close()


def complete_goal_today(chat_id, goal_id):
    """Mark goal as done for today"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection error"
    
    cursor = connection.cursor(dictionary=True)
    try:
        today = date.today()
        
        # Get current goal
        cursor.execute("""
            SELECT goal_id as id, goal, target_days, streak, last_checkin
            FROM goals 
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        goal = cursor.fetchone()
        
        if not goal:
            return False, "Goal not found!"
        
        # Check if already completed today
        if goal['last_checkin'] and goal['last_checkin'] == today:
            return False, "Already checked in today! ✅"
        
        # Increment streak
        new_streak = goal['streak'] + 1
        
        # Check if goal is now completed
        if new_streak >= goal['target_days']:
            cursor.execute("""
                UPDATE goals 
                SET streak = %s, last_checkin = %s, status = 'completed', completed_date = %s
                WHERE chat_id = %s AND goal_id = %s
            """, (new_streak, today, today, chat_id, goal_id))
            connection.commit()
            
            return True, (
                f"🎉🎉🎉 **GOAL COMPLETED!** 🎉🎉🎉\n\n"
                f"You've reached your {goal['target_days']}-day target for:\n"
                f"**{goal['goal']}**\n\n"
                f"🔥 Final streak: {new_streak} days\n"
                f"🏆 This goal is now complete!\n\n"
                f"View all achievements: /completedgoals"
            )
        else:
            # Just update streak
            cursor.execute("""
                UPDATE goals 
                SET streak = %s, last_checkin = %s
                WHERE chat_id = %s AND goal_id = %s
            """, (new_streak, today, chat_id, goal_id))
            connection.commit()
            
            days_left = goal['target_days'] - new_streak
            return True, f"Great! {new_streak} day streak on '{goal['goal']}'! 🔥\n\nOnly {days_left} days to go!"
        
    finally:
        cursor.close()
        connection.close()


def update_goal_name(chat_id, goal_id, new_name):
    """Update goal name"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE goals 
            SET goal = %s 
            WHERE chat_id = %s AND goal_id = %s
        """, (new_name, chat_id, goal_id))
        
        connection.commit()
        return cursor.rowcount > 0
        
    finally:
        cursor.close()
        connection.close()


def update_goal_days(chat_id, goal_id, new_target_days):
    """Update goal target days and adjust status"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Get current goal streak
        cursor.execute("""
            SELECT streak 
            FROM goals 
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        goal = cursor.fetchone()
        if not goal:
            return False
        
        # Update status based on streak vs new target
        if goal['streak'] < new_target_days:
            # Reactivate if streak is less than new target
            cursor.execute("""
                UPDATE goals 
                SET target_days = %s, status = 'active', completed_date = NULL
                WHERE chat_id = %s AND goal_id = %s
            """, (new_target_days, chat_id, goal_id))
        else:
            # Keep completed if streak already meets/exceeds new target
            cursor.execute("""
                UPDATE goals 
                SET target_days = %s, status = 'completed',
                    completed_date = COALESCE(completed_date, CURRENT_DATE)
                WHERE chat_id = %s AND goal_id = %s
            """, (new_target_days, chat_id, goal_id))
        
        connection.commit()
        return True
        
    finally:
        cursor.close()
        connection.close()


def update_goal_reminders(chat_id, goal_id, reminder_times):
    """Update goal reminder times"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE goals 
            SET reminder_times = %s 
            WHERE chat_id = %s AND goal_id = %s
        """, (json.dumps(reminder_times), chat_id, goal_id))
        
        connection.commit()
        return cursor.rowcount > 0
        
    finally:
        cursor.close()
        connection.close()


def delete_goal(chat_id, goal_id):
    """Delete a goal"""
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            DELETE FROM goals 
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        connection.commit()
        
    finally:
        cursor.close()
        connection.close()


def mark_goal_complete(chat_id, goal_id):
    """Manually mark goal as completed"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection error"
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Get goal name
        cursor.execute("""
            SELECT goal 
            FROM goals 
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        goal = cursor.fetchone()
        if not goal:
            return False, "Goal not found!"
        
        # Mark as completed
        cursor.execute("""
            UPDATE goals 
            SET status = 'completed', 
                completed_date = COALESCE(completed_date, CURRENT_DATE)
            WHERE chat_id = %s AND goal_id = %s
        """, (chat_id, goal_id))
        
        connection.commit()
        return True, f"🎉 Goal completed: {goal['goal']}"
        
    finally:
        cursor.close()
        connection.close()
