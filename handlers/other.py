from telegram import Update
from telegram.ext import ContextTypes
from services.ai_response import chat_with_ai, update_goal_progress, update_habit_progress
from services.ui_service import render_main_menu, render_support_screen, render_combined_stats_card, render_detailed_progress_screen
from handlers.start import get_main_keyboard

async def other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text
    user_name = update.effective_user.first_name or "friend"
    
    # Handle menu button presses with beautiful screens + persistent keyboard
    if user_message == "🎯 My Goals":
        from handlers.goals import goals
        await goals(update, context)
        
    elif user_message == "🔄 My Habits":
        from handlers.habits import habits  
        await habits(update, context)
        
    elif user_message == "📈 My Progress":
        # Render progress screen (visual + AI feedback)
        progress_screen = render_detailed_progress_screen(chat_id)
        
        # Instead of empty markdown, send a simple heading or skip
        await update.message.reply_text("📊 Here's your progress overview:", reply_markup=get_main_keyboard())
        
        response = chat_with_ai(
            "Give me a detailed analysis of my progress, insights, and specific suggestions for improvement based on my current goals and habits performance.",
            chat_id
        )
        await update.message.reply_text(f"📈 **Detailed Progress Analysis:**\n\n{response}", parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    elif user_message == "💙 Need Support":
        support_screen = render_support_screen(chat_id)
        await update.message.reply_text("💙 I'm here for you. Here's your support screen:", reply_markup=get_main_keyboard())
        
        response = chat_with_ai("I need emotional support and someone to talk to", chat_id)
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
        
    elif user_message == "✨ Daily Boost":
        response = chat_with_ai("Give me daily motivation and a boost of energy", chat_id)
        await update.message.reply_text(
            f"✨ **Daily Boost for {user_name}** ✨\n\n{response}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    elif user_message == "💬 Free Chat":
        response = chat_with_ai("I want to have a free conversation with my AI friend", chat_id)
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
        
    elif any(phrase in user_message.lower() for phrase in ["goal done", "completed goal", "finished goal"]):
        response = update_goal_progress(chat_id, completed=True)
        await update.message.reply_text(f"🎉 {response}", reply_markup=get_main_keyboard())
        
    elif any(phrase in user_message.lower() for phrase in ["habit done", "completed habit", "did habit"]):
        response = update_habit_progress(chat_id, completed=True)
        await update.message.reply_text(f"✅ {response}", reply_markup=get_main_keyboard())
        
    else:
        # Free chat fallback
        response = chat_with_ai(user_message, chat_id)
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
