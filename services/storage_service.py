import json
import os
from datetime import date


DATA_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    
    try:
        with open(DATA_FILE, "r") as f:
            content = f.read().strip()
            if not content:  # Empty file
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        # File is corrupted, backup and recreate
        print(f"⚠️ Warning: users.json corrupted. Creating backup and new file.")
        if os.path.exists(DATA_FILE):
            backup_file = DATA_FILE + ".backup"
            os.rename(DATA_FILE, backup_file)
            print(f"💾 Old file backed up to: {backup_file}")
        
        # Create fresh file
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}



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
        'reminder_times': reminder_times or ["09:00"]
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
            
            # Increment streak
            goal['streak'] = goal.get('streak', 0) + 1
            goal['last_checkin'] = today
            
            # 🔥 AUTO-COMPLETE when target reached
            if goal['streak'] >= goal.get('target_days', 30):
                goal['status'] = 'completed'
                goal['completed_date'] = today
                save_user(chat_id, user)
                return True, (
                    f"🎉🎉🎉 **GOAL COMPLETED!** 🎉🎉🎉\n\n"
                    f"You've reached your {goal['target_days']}-day target for:\n"
                    f"**{goal['goal']}**\n\n"
                    f"🔥 Final streak: {goal['streak']} days\n"
                    f"🏆 This goal is now complete!\n\n"
                    f"View all achievements: /completedgoals"
                )
            
            save_user(chat_id, user)
            days_left = goal['target_days'] - goal['streak']
            return True, f"Great! {goal['streak']} day streak on '{goal['goal']}'! 🔥\n\nOnly {days_left} days to go!"
    
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


# ===== GOAL UPDATE OPERATIONS (FOR EDITING) =====
def update_goal_name(chat_id, goal_id, new_name):
    """Update the name of a specific goal"""
    user = get_user(chat_id)
    for goal in user.get('goals', []):
        if isinstance(goal, dict) and goal['id'] == goal_id:
            goal['goal'] = new_name
            save_user(chat_id, user)
            return True
    return False


def update_goal_days(chat_id, goal_id, new_target_days):
    """Update the target days of a specific goal"""
    user = get_user(chat_id)
    for goal in user.get('goals', []):
        if isinstance(goal, dict) and goal['id'] == goal_id:
            goal['target_days'] = new_target_days
            
            # 🔥 FIX: Re-activate goal if streak is less than new target
            if goal['streak'] < new_target_days:
                goal['status'] = 'active'
                # Remove completed_date since it's active again
                if 'completed_date' in goal:
                    del goal['completed_date']
            # Auto-complete if streak already exceeds new target
            elif goal['streak'] >= new_target_days:
                goal['status'] = 'completed'
                if 'completed_date' not in goal:
                    goal['completed_date'] = date.today().isoformat()
            
            save_user(chat_id, user)
            return True
    return False



def update_goal_reminders(chat_id, goal_id, reminder_times):
    """Update the reminder times of a specific goal"""
    user = get_user(chat_id)
    for goal in user.get('goals', []):
        if isinstance(goal, dict) and goal['id'] == goal_id:
            goal['reminder_times'] = reminder_times
            save_user(chat_id, user)
            return True
    return False


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
        'reminder_times': reminder_times or ["09:00"],
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
            
            # Increment streak
            habit['streak'] = habit.get('streak', 0) + 1
            habit['last_completed'] = today
            
            # 🔥 AUTO-COMPLETE at 21 days
            if habit['streak'] >= 21:
                habit['status'] = 'completed'
                habit['completed_date'] = today
                save_user(chat_id, user)
                return True, (
                    f"🎉🎉🎉 **21-DAY CHALLENGE COMPLETE!** 🎉🎉🎉\n\n"
                    f"You've mastered: **{habit['habit']}**\n\n"
                    f"🏆 This habit is now part of who you are!\n"
                    f"🔥 Final streak: 21 days\n\n"
                    f"View all achievements: /completedhabits"
                )
            
            save_user(chat_id, user)
            days_left = 21 - habit['streak']
            return True, f"Awesome! {habit['streak']} day streak on '{habit['habit']}'! 💪\n\n{days_left} days to go!"
    
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


# ===== HABIT UPDATE OPERATIONS (FOR EDITING) =====
def update_habit_name(chat_id, habit_id, new_name):
    """Update the name of a specific habit"""
    user = get_user(chat_id)
    for habit in user.get('habits', []):
        if isinstance(habit, dict) and habit['id'] == habit_id:
            habit['habit'] = new_name
            save_user(chat_id, user)
            return True
    return False


def update_habit_streak(chat_id, habit_id, new_streak):
    """Update the streak/days of a specific habit"""
    user = get_user(chat_id)
    for habit in user.get('habits', []):
        if isinstance(habit, dict) and habit['id'] == habit_id:
            habit['streak'] = new_streak
            # Update status if streak reaches 21
            if new_streak >= 21:
                habit['status'] = 'completed'
            else:
                habit['status'] = 'active'
            save_user(chat_id, user)
            return True
    return False


def update_habit_reminders(chat_id, habit_id, reminder_times):
    """Update the reminder times of a specific habit"""
    user = get_user(chat_id)
    for habit in user.get('habits', []):
        if isinstance(habit, dict) and habit['id'] == habit_id:
            habit['reminder_times'] = reminder_times
            save_user(chat_id, user)
            return True
    return False

def get_user_profile(chat_id):
    """Get user profile data"""
    data = load_data()
    user = data.get(str(chat_id), {})
    return {
        'name': user.get('name', None),
        'country': user.get('country', None),
        'timezone': user.get('timezone', 'UTC'),
        'onboarded': user.get('onboarded', False)
    }


def set_user_profile(chat_id, name, country, timezone):
    """Set user profile after onboarding"""
    data = load_data()
    if str(chat_id) not in data:
        data[str(chat_id)] = {'goals': [], 'habits': []}
    
    data[str(chat_id)]['name'] = name
    data[str(chat_id)]['country'] = country
    data[str(chat_id)]['timezone'] = timezone
    data[str(chat_id)]['onboarded'] = True
    save_data(data)
    return True


def is_user_onboarded(chat_id):
    """Check if user has completed onboarding"""
    data = load_data()
    user = data.get(str(chat_id), {})
    return user.get('onboarded', False)


def set_user_timezone(chat_id, timezone_name):
    """Set timezone for a user"""
    data = load_data()
    if str(chat_id) not in data:
        data[str(chat_id)] = {'goals': [], 'habits': []}
    data[str(chat_id)]['timezone'] = timezone_name
    save_data(data)
    return True


def get_user_timezone(chat_id):
    """Get user's timezone, default to UTC if not set"""
    data = load_data()
    user = data.get(str(chat_id), {})
    return user.get('timezone', 'UTC')

