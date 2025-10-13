"""
Database Package
Import everything from here
"""

from .connection import get_db_connection, test_connection
from .tables import init_all_tables
# Mood operations
from .mood_db import save_mood, get_weekly_moods, save_conversation, get_weekly_conversations



# User operations
from .user_db import (
    get_user, save_user, get_user_profile, set_user_profile,
    is_user_onboarded, get_user_timezone, set_user_timezone
)

# Goal operations
from .goal_db import (
    add_goal, get_all_goals, get_goal_by_id, complete_goal_today,
    update_goal_name, update_goal_days, update_goal_reminders,
    delete_goal, mark_goal_complete
)

# Habit operations
from .habit_db import (
    add_habit, get_all_habits, get_habit_by_id, complete_habit_today,
    update_habit_name, update_habit_streak, update_habit_reminders,
    delete_habit, mark_habit_complete
)

# Utility
from .user_db import load_data

from .premium_db import (
    is_premium_user, activate_premium, track_daily_progress,
    get_weekly_stats, award_badge, get_user_badges
)




# Auto-initialize database on import
init_all_tables()
