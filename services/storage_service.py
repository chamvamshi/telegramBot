import json
import os
from datetime import date

DATA_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(chat_id):
    data = load_data()
    user = data.get(str(chat_id), {})
    if 'goals' not in user:
        user['goals'] = []
    if 'habits' not in user:
        user['habits'] = []
    return user

def save_user(chat_id, user_data):
    data = load_data()
    data[str(chat_id)] = user_data
    save_data(data)

# ===== GOAL OPERATIONS =====
def add_goal(chat_id, goal_text, target_days=30, motivation_line="", reminder_times=None):
    """Add a new goal with custom reminder times"""
    user = get_user(chat_id)
    goal_id = len(user['goals']) + 1
    new_goal = {
        'id': goal_id,
        'goal': goal_text,
        'target_days': target_days,
        'streak': 0,
        'start_date': date.today().isoformat(),
        'motivation': motivation_line or f"Stay focused on: {goal_text}",
        'last_checkin': None,
        'status': 'active',
        'reminder_times': reminder_times or ["09:00"]  # NEW: Multiple reminder times
    }
    user['goals'].append(new_goal)
    save_user(chat_id, user)
    return goal_id

def get_all_goals(chat_id, status='active'):
    user = get_user(chat_id)
    if not isinstance(user.get('goals'), list):
        user['goals'] = []
        save_user(chat_id, user)
        return []
    return [g for g in user['goals'] if isinstance(g, dict) and g.get('status') == status]

def get_goal_by_id(chat_id, goal_id):
    user = get_user(chat_id)
    for goal in user.get('goals', []):
        if isinstance(goal, dict) and goal['id'] == goal_id:
            return goal
    return None

def complete_goal_today(chat_id, goal_id):
    user = get_user(chat_id)
    today = date.today().isoformat()
    for goal in user['goals']:
        if goal['id'] == goal_id:
            if goal.get('last_checkin') == today:
                return False, "Already checked in today! ✅"
            goal['streak'] = goal.get('streak', 0) + 1
            goal['last_checkin'] = today
            save_user(chat_id, user)
            return True, f"Great! {goal['streak']} day streak on '{goal['goal']}'! 🔥"
    return False, "Goal not found!"

def delete_goal(chat_id, goal_id):
    user = get_user(chat_id)
    user['goals'] = [g for g in user['goals'] if g.get('id') != goal_id]
    save_user(chat_id, user)

def mark_goal_complete(chat_id, goal_id):
    user = get_user(chat_id)
    for goal in user['goals']:
        if goal['id'] == goal_id:
            goal['status'] = 'completed'
            save_user(chat_id, user)
            return True, f"🎉 Goal completed: {goal['goal']}"
    return False, "Goal not found!"

# ===== HABIT OPERATIONS =====
def add_habit(chat_id, habit_text, reminder_times=None):
    """Add a new habit with custom reminder times"""
    user = get_user(chat_id)
    habit_id = len(user['habits']) + 1
    new_habit = {
        'id': habit_id,
        'habit': habit_text,
        'days_target': 21,
        'streak': 0,
        'start_date': date.today().isoformat(),
        'reminder_times': reminder_times or ["09:00"],  # NEW: Multiple reminder times
        'last_completed': None,
        'status': 'active'
    }
    user['habits'].append(new_habit)
    save_user(chat_id, user)
    return habit_id

def get_all_habits(chat_id, status='active'):
    user = get_user(chat_id)
    if not isinstance(user.get('habits'), list):
        user['habits'] = []
        save_user(chat_id, user)
        return []
    return [h for h in user['habits'] if isinstance(h, dict) and h.get('status') == status]

def get_habit_by_id(chat_id, habit_id):
    user = get_user(chat_id)
    for habit in user.get('habits', []):
        if isinstance(habit, dict) and habit['id'] == habit_id:
            return habit
    return None

def complete_habit_today(chat_id, habit_id):
    user = get_user(chat_id)
    today = date.today().isoformat()
    for habit in user['habits']:
        if habit['id'] == habit_id:
            if habit.get('last_completed') == today:
                return False, "Already completed today! ✅"
            habit['streak'] = habit.get('streak', 0) + 1
            habit['last_completed'] = today
            days_left = habit['days_target'] - habit['streak']
            if days_left <= 0:
                habit['status'] = 'completed'
                save_user(chat_id, user)
                return True, f"🏆 21-DAY CHALLENGE COMPLETE! You mastered '{habit['habit']}'! 🎉"
            save_user(chat_id, user)
            return True, f"Awesome! {habit['streak']} day streak on '{habit['habit']}'! {days_left} days to go! 💪"
    return False, "Habit not found!"

def delete_habit(chat_id, habit_id):
    user = get_user(chat_id)
    user['habits'] = [h for h in user['habits'] if h.get('id') != habit_id]
    save_user(chat_id, user)

def mark_habit_complete(chat_id, habit_id):
    user = get_user(chat_id)
    for habit in user['habits']:
        if habit['id'] == habit_id:
            habit['status'] = 'completed'
            save_user(chat_id, user)
            return True, f"🎉 Habit mastered: {habit['habit']}"
    return False, "Habit not found!"
