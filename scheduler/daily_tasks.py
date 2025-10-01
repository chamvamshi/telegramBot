import asyncio
from services.storage_service import load_data
from services.ai_response import get_motivation
from telegram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)

async def schedule_daily_reminders():
    """Send daily reminders to all users"""
    while True:
        try:
            data = load_data()
            for chat_id, user in data.items():
                try:
                    if "goal" in user:
                        mot = get_motivation(user['goal'])
                        await bot.send_message(
                            chat_id, 
                            f"🎯 **Goal Reminder:**\n{user['goal']}\n\n💪 {mot}",
                            parse_mode='Markdown'
                        )

                    if "habit" in user and user.get("habit_days_left", 0) > 0:
                        mot = get_motivation(user['habit'])
                        streak = user.get("habit_streak", 0)
                        await bot.send_message(
                            chat_id, 
                            f"🔄 **Habit Reminder:**\n{user['habit']}\n\nStreak: {streak} days\n💪 {mot}",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    print(f"Failed to send reminder to {chat_id}: {e}")
                    
        except Exception as e:
            print(f"Error in reminder scheduler: {e}")
            
        # Wait 8 hours (3 times per day)
        await asyncio.sleep(8 * 60 * 60)
