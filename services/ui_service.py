from services.storage_service import get_user, get_all_goals, get_all_habits


def create_progress_bar(current, total, width=20, filled_char="█", empty_char="░"):
    """Create visual progress bar"""
    if total == 0:
        return empty_char * width
    
    filled_length = int(width * current / total)
    bar = filled_char * filled_length + empty_char * (width - filled_length)
    percentage = int((current / total) * 100)
    return f"{bar} {percentage}%"


def create_streak_display(streak):
    """Create visual streak display"""
    fire_emojis = min(streak // 3, 10)
    return "🔥" * fire_emojis + f" {streak} days"


def render_main_menu(chat_id, user_name="friend"):
    """Render beautiful main menu screen with multiple goals/habits support"""
    goals = get_all_goals(chat_id)
    habits = get_all_habits(chat_id)
    
    # Count totals
    total_goal_streak = sum(g['streak'] for g in goals)
    total_habit_streak = sum(h['streak'] for h in habits)
    
    goal_text = f"🎯 {len(goals)} Goal(s): {total_goal_streak} days ✅" if goals else "🎯 No goals set"
    habit_text = f"🔄 {len(habits)} Habit(s): {total_habit_streak} days 🔥" if habits else "🔄 No habits set"
    
    screen = f"""╭─────────────────────────────╮
│  🌟 SoulFriend - Your AI    │
│     Accountability Partner   │
├─────────────────────────────┤
│                             │
│  Hey {user_name}! 👋               │
│  Ready to crush your goals? │
│                             │
│  📊 Today's Progress:       │
│  {goal_text:<27}│
│  {habit_text:<27}│
│                             │
╰─────────────────────────────╯"""
    
    return screen


def render_goal_progress_card(chat_id):
    """Render ALL goals progress"""
    goals = get_all_goals(chat_id)
    
    if not goals:
        return """╭─────────────────────────────╮
│        🎯 SET A GOAL        │
├─────────────────────────────┤
│                             │
│   No active goal yet! 🚀    │
│                             │
│   Ready to start your       │
│   accountability journey?   │
│                             │
│   💡 Try: /addgoal          │
│                             │
╰─────────────────────────────╯"""
    
    # Build card for all goals
    card = f"╭─────────────────────────────╮\n"
    card += f"│   🎯 YOUR GOALS ({len(goals)})         │\n"
    card += f"├─────────────────────────────┤\n"
    
    for goal in goals:
        progress = (goal['streak'] / goal['target_days']) * 100 if goal['target_days'] > 0 else 0
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        
        # Truncate goal name if too long
        goal_name = goal['goal'][:20] if len(goal['goal']) > 20 else goal['goal']
        
        card += f"│                             │\n"
        card += f"│ {goal['id']}. {goal_name:<20}    │\n"
        card += f"│ [{progress_bar}] {int(progress)}%   │\n"
        card += f"│ 🔥 {goal['streak']}/{goal['target_days']} days             │\n"
    
    card += f"│                             │\n"
    card += f"│ Use /goalinfo <id> to view  │\n"
    card += f"│ Use /goaldone <id> to check │\n"
    card += f"│                             │\n"
    card += f"╰─────────────────────────────╯"
    
    return card


def render_habit_progress_card(chat_id):
    """Render ALL habits progress"""
    habits = get_all_habits(chat_id)
    
    if not habits:
        return """╭─────────────────────────────╮
│       🔄 BUILD HABITS       │
├─────────────────────────────┤
│                             │
│   No habit tracker yet! 🌱  │
│                             │
│   21 days to build a        │
│   life-changing habit!      │
│                             │
│   💡 Try: /addhabit         │
│                             │
╰─────────────────────────────╯"""
    
    # Build card for all habits
    card = f"╭─────────────────────────────╮\n"
    card += f"│   🔄 YOUR HABITS ({len(habits)})       │\n"
    card += f"├─────────────────────────────┤\n"
    
    for habit in habits:
        progress = (habit['streak'] / 21) * 100
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        days_left = 21 - habit['streak']
        
        # Truncate habit name if too long
        habit_name = habit['habit'][:20] if len(habit['habit']) > 20 else habit['habit']
        
        card += f"│                             │\n"
        card += f"│ {habit['id']}. {habit_name:<20}    │\n"
        card += f"│ [{progress_bar}] {int(progress)}%   │\n"
        card += f"│ 🔥 {habit['streak']}/21 days ({days_left} left) │\n"
    
    card += f"│                             │\n"
    card += f"│ Use /habitinfo <id> to view │\n"
    card += f"│ Use /habitdone <id> to mark │\n"
    card += f"│                             │\n"
    card += f"╰─────────────────────────────╯"
    
    return card


def render_detailed_progress_screen(chat_id):
    """Render comprehensive progress overview with multiple goals/habits"""
    goals = get_all_goals(chat_id)
    habits = get_all_habits(chat_id)
    
    if not goals and not habits:
        return """╭─────────────────────────────╮
│      📈 MY PROGRESS         │
├─────────────────────────────┤
│                             │
│   No active goals or habits │
│   yet! Start your journey:  │
│                             │
│   🎯 /addgoal               │
│   🔄 /addhabit              │
│                             │
╰─────────────────────────────╯"""
    
    # Calculate overall stats
    total_goal_streak = sum(g['streak'] for g in goals)
    total_habit_streak = sum(h['streak'] for h in habits)
    overall_score = 0
    
    if goals:
        goal_score = sum((g['streak'] / g['target_days']) * 100 for g in goals) / len(goals)
        overall_score += goal_score / 2
    
    if habits:
        habit_score = sum((h['streak'] / 21) * 100 for h in habits) / len(habits)
        overall_score += habit_score / 2
    
    overall_score = int(overall_score)
    
    # Motivation level
    if overall_score >= 80:
        motivation_level = "🔥 ON FIRE!"
    elif overall_score >= 60:
        motivation_level = "💪 STRONG"
    elif overall_score >= 40:
        motivation_level = "⚡ BUILDING"
    elif overall_score >= 20:
        motivation_level = "🌱 GROWING"
    else:
        motivation_level = "🚀 STARTING"
    
    card = f"""╭─────────────────────────────╮
│      📈 MY PROGRESS         │
├─────────────────────────────┤
│                             │
│ 🎯 GOALS: {len(goals)} active          │"""
    
    for goal in goals[:3]:  # Show first 3 goals
        card += f"\n│   • {goal['goal'][:22]:<22} │"
        card += f"\n│     {goal['streak']}/{goal['target_days']} days              │"
    
    if len(goals) > 3:
        card += f"\n│   ... and {len(goals) - 3} more          │"
    
    card += f"""
│                             │
│ 🔄 HABITS: {len(habits)} active         │"""
    
    for habit in habits[:3]:  # Show first 3 habits
        card += f"\n│   • {habit['habit'][:22]:<22} │"
        card += f"\n│     {habit['streak']}/21 days            │"
    
    if len(habits) > 3:
        card += f"\n│   ... and {len(habits) - 3} more         │"
    
    card += f"""
│                             │
│ 📊 OVERALL SCORE: {overall_score}/100     │
│ 🎯 MOTIVATION: {motivation_level}     │
│                             │
│ 🏆 TOTAL STREAKS            │
│ Goals: {total_goal_streak} days            │
│ Habits: {total_habit_streak} days           │
│                             │
╰─────────────────────────────╯"""
    
    return card
