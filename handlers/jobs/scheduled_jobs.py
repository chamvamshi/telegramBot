"""
Scheduled Jobs Module
All background tasks and automated reports
"""

from datetime import datetime, timedelta, date
from database.premium_db import (
    is_premium_user, track_daily_progress, get_weekly_stats, award_badge
)
from database import load_data, get_user_profile, get_all_goals, get_all_habits
from services.chart_generator import create_3day_feedback_chart, create_weekly_progress_chart
from services.ai_analytics import generate_weekly_analysis, generate_3day_feedback

# ===== JOB: Weekly Reports =====
async def send_weekly_reports(context):
    """Send weekly progress reports to all premium users (Every Sunday 8 PM)"""
    print("📊 Sending weekly reports to premium users...")
    
    data = load_data()
    report_count = 0
    
    for chat_id_str, user in data.items():
        chat_id = int(chat_id_str)
        
        if not is_premium_user(chat_id):
            continue
        
        try:
            profile = get_user_profile(chat_id)
            user_name = profile.get('name', 'friend')
            
            # Get stats
            stats = get_weekly_stats(chat_id)
            
            if not stats or stats.get('total_goals', 0) + stats.get('total_habits', 0) == 0:
                continue
            
            # Generate chart
            chart_buf = create_weekly_progress_chart(chat_id, stats, user_name)
            
            # Calculate completion
            goals_completed = stats.get('goals_completed', 0)
            habits_completed = stats.get('habits_completed', 0)
            total_goals = stats.get('total_goals', 1)
            total_habits = stats.get('total_habits', 1)
            
            completion_rate = ((goals_completed + habits_completed) / 
                              (total_goals + total_habits) * 100) if (total_goals + total_habits) > 0 else 0
            
            # Award badge
            badge = None
            badge_emoji = None
            badge_type = None
            
            if completion_rate >= 90:
                badge = "Soul Diamond"
                badge_emoji = "💎"
                badge_type = 'soul_diamond'
            elif completion_rate >= 80:
                badge = "Soul Gold"
                badge_emoji = "🥇"
                badge_type = 'soul_gold'
            elif completion_rate >= 50:
                badge = "Soul Silver"
                badge_emoji = "🥈"
                badge_type = 'soul_silver'
            
            if badge_type:
                award_badge(chat_id, badge_type, completion_rate)
            
            # AI insights
            ai_insights = generate_weekly_analysis(chat_id, stats, user_name)
            
            # Create report
            report = f"""
╔═══════════════════════════════╗
║  📊 **WEEKLY PROGRESS REPORT** ║
╚═══════════════════════════════╝

**Hey {user_name}!** Your week is complete!

📈 **Performance:**
• Completion Rate: **{completion_rate:.1f}%**
• Goals: {goals_completed}/{total_goals} ✅
• Habits: {habits_completed}/{total_habits} ✅

{f'🏆 **New Achievement!**\\n{badge_emoji} **{badge}** badge earned!' if badge else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 **AI Insights:**

{ai_insights}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Have an amazing week ahead! 💪
"""
            
            # Send
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=chart_buf,
                caption=report,
                parse_mode='Markdown'
            )
            
            report_count += 1
            print(f"✅ Report sent to user {chat_id}")
            
        except Exception as e:
            print(f"❌ Error sending report to {chat_id}: {e}")
    
    print(f"📊 Weekly reports sent: {report_count}")

# ===== JOB: 3-Day Pattern Detection =====
async def check_3day_patterns(context):
    """Detect 3-day inactivity patterns (Premium only, Daily at 6 PM)"""
    print("💭 Checking 3-day patterns...")
    
    data = load_data()
    today = date.today()
    three_days_ago = today - timedelta(days=3)
    alert_count = 0
    
    for chat_id_str, user in data.items():
        chat_id = int(chat_id_str)
        
        if not is_premium_user(chat_id):
            continue
        
        try:
            goals = get_all_goals(chat_id, status='active')
            habits = get_all_habits(chat_id, status='active')
            
            # Check goals
            for goal in goals:
                last_checkin = goal.get('last_checkin')
                if last_checkin:
                    last_date = datetime.strptime(last_checkin, '%Y-%m-%d').date()
                    if last_date <= three_days_ago:
                        # Generate chart (simplified history)
                        history = []  # Can be enhanced with actual DB query
                        chart_buf = create_3day_feedback_chart(chat_id, goal, history, type='goal')
                        
                        # AI feedback
                        ai_feedback = generate_3day_feedback(goal, type='goal')
                        
                        caption = f"""
💭 **3-Day Pattern Alert**

**Goal:** {goal['goal']}

{ai_feedback}

Let's get back on track! 🎯
"""
                        
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=chart_buf,
                            caption=caption,
                            parse_mode='Markdown'
                        )
                        alert_count += 1
            
            # Check habits (similar)
            for habit in habits:
                last_completed = habit.get('last_completed')
                if last_completed:
                    last_date = datetime.strptime(last_completed, '%Y-%m-%d').date()
                    if last_date <= three_days_ago:
                        history = []
                        chart_buf = create_3day_feedback_chart(chat_id, habit, history, type='habit')
                        ai_feedback = generate_3day_feedback(habit, type='habit')
                        
                        caption = f"""
💭 **3-Day Pattern Alert**

**Habit:** {habit['habit']}

{ai_feedback}

Small steps matter! 💪
"""
                        
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=chart_buf,
                            caption=caption,
                            parse_mode='Markdown'
                        )
                        alert_count += 1
                        
        except Exception as e:
            print(f"❌ Error checking patterns for {chat_id}: {e}")
    
    print(f"💭 Pattern alerts sent: {alert_count}")

# ===== JOB: Daily Tracking =====
async def track_all_users_daily(context):
    """Track daily progress for all users (Daily at 11:59 PM)"""
    print("📊 Tracking daily progress for all users...")
    
    data = load_data()
    count = 0
    
    for chat_id_str in data.keys():
        chat_id = int(chat_id_str)
        try:
            track_daily_progress(chat_id)
            count += 1
        except Exception as e:
            print(f"❌ Error tracking {chat_id}: {e}")
    
    print(f"📊 Daily tracking complete: {count} users")

# Export all job functions
def get_scheduled_jobs():
    """Return list of (job_function, schedule_config) tuples"""
    from datetime import time
    import pytz
    
    return [
        # Weekly reports every Sunday at 8 PM UTC
        {
            'callback': send_weekly_reports,
            'trigger': 'cron',
            'day_of_week': 'sun',
            'hour': 20,
            'minute': 0,
            'timezone': pytz.UTC,
            'name': 'weekly_reports'
        },
        # 3-day patterns daily at 6 PM UTC
        {
            'callback': check_3day_patterns,
            'trigger': 'daily',
            'time': time(hour=18, minute=0, tzinfo=pytz.UTC),
            'name': '3day_patterns'
        },
        # Daily tracking at 11:59 PM UTC
        {
            'callback': track_all_users_daily,
            'trigger': 'daily',
            'time': time(hour=23, minute=59, tzinfo=pytz.UTC),
            'name': 'daily_tracking'
        }
    ]
