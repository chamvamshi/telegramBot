#services/ai_response
from openai import OpenAI
from config import OPENROUTER_API_KEY
from services.storage_service import get_user, save_user
import json
from datetime import datetime

# Initialize OpenRouter client using OpenAI SDK
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:5000",  # Required by OpenRouter
        "X-Title": "SoulFriend Bot"  # Optional: appears in OpenRouter dashboard
    }
)

def get_user_context(chat_id):
    """Get user's current context for AI conversations"""
    user = get_user(chat_id)
    context = {
        "goals": user.get("goal", "No goals set"),
        "goal_streak": user.get("goal_streak", 0),
        "goal_target_days": user.get("goal_target_days", 30),
        "habits": user.get("habit", "No habits set"), 
        "habit_streak": user.get("habit_streak", 0),
        "habit_days_left": user.get("habit_days_left", 21),
        "last_mood": user.get("last_mood", "Unknown"),
        "conversation_history": user.get("conversation_history", [])
    }
    return context, user

def save_conversation(chat_id, user_message, ai_response, user_data):
    """Save conversation for context continuity"""
    if "conversation_history" not in user_data:
        user_data["conversation_history"] = []
    
    user_data["conversation_history"].append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "ai": ai_response
    })
    
    # Keep only last 10 conversations for context
    if len(user_data["conversation_history"]) > 10:
        user_data["conversation_history"] = user_data["conversation_history"][-10:]
    
    save_user(chat_id, user_data)

def chat_with_ai(user_message, chat_id, model="anthropic/claude-3-haiku"):
    """Main AI conversation function using OpenRouter - handles everything dynamically"""
    context, user_data = get_user_context(chat_id)
    
    # Build conversation history for context
    recent_messages = []
    for conv in context["conversation_history"][-3:]:  # Last 3 conversations
        recent_messages.append(f"User: {conv['user']}")
        recent_messages.append(f"Assistant: {conv['ai']}")
    
    conversation_context = "\n".join(recent_messages) if recent_messages else "This is our first conversation."
    
    system_prompt = f"""You are SoulFriend, a caring 24/7 accountability companion and emotional support friend. 

USER'S CURRENT STATUS:
- Goals: {context['goals']} (Streak: {context['goal_streak']} days, Target: {context['goal_target_days']} days)
- Habits: {context['habits']} (Streak: {context['habit_streak']} days, {context['habit_days_left']} days left)  
- Last mood: {context['last_mood']}

RECENT CONVERSATION:
{conversation_context}

YOUR PERSONALITY:
- Warm, supportive, and genuinely caring like a best friend
- Remember their goals/habits and reference them naturally in conversation
- Ask follow-up questions to keep conversations flowing
- Offer practical, actionable advice based on their situation
- If they seem lost or unmotivated, gently guide them toward their goals/habits
- Celebrate their progress enthusiastically and be understanding of setbacks
- Be conversational and natural, not robotic or formal
- Use emojis appropriately to show warmth

RESPOND NATURALLY to whatever they say. Handle:
- Goals/Habits: Give accountability, track progress, motivate specifically
- Feelings/Emotions: Listen empathetically, provide genuine support
- General conversation: Be a good friend, relate to their journey when relevant
- Requests for advice: Give thoughtful, personalized suggestions
- Daily check-ins: Ask about their progress and how they're feeling

Keep responses warm, personal, and under 150 words unless they specifically ask for detailed advice."""

    try:
        response = client.chat.completions.create(
            model=model,  # Can use: anthropic/claude-3-haiku, openai/gpt-3.5-turbo, meta-llama/llama-3.1-8b-instruct, etc.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
      #  print(f"✅ OpenRouter AI Response ({model}): {ai_response[:100]}...")  # Debug log
        
        # Save this conversation
        save_conversation(chat_id, user_message, ai_response, user_data)
        
        return ai_response
        
    except Exception as e:
        print(f"❌ OpenRouter API Error: {e}")
        return f"I'm having trouble connecting right now, but I'm still here for you! Can you tell me more about what's on your mind? 💙"

def update_goal_progress(chat_id, goal_text=None, completed=False):
    """Update goal and return AI response"""
    user = get_user(chat_id)
    
    if goal_text:
        # Parse target days if provided
        parts = goal_text.split()
        if parts[-1].isdigit():
            target_days = int(parts[-1])
            goal_text = " ".join(parts[:-1])
        else:
            target_days = 30
            
        user["goal"] = goal_text
        user["goal_streak"] = 0
        user["goal_target_days"] = target_days
        user["goal_start_date"] = datetime.now().strftime("%Y-%m-%d")
        save_user(chat_id, user)
        return chat_with_ai(f"I just set a new goal: {goal_text} for {target_days} days", chat_id)
    
    if completed:
        user["goal_streak"] = user.get("goal_streak", 0) + 1
        user["goal_last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_user(chat_id, user)
        return chat_with_ai(f"I completed my goal today: {user['goal']}. This is day {user['goal_streak']}!", chat_id)

def update_habit_progress(chat_id, habit_text=None, completed=False):
    """Update habit and return AI response"""
    user = get_user(chat_id)
    
    if habit_text:
        user["habit"] = habit_text
        user["habit_streak"] = 0
        user["habit_days_left"] = 21
        user["habit_start_date"] = datetime.now().strftime("%Y-%m-%d")
        save_user(chat_id, user)
        return chat_with_ai(f"I want to build this new habit: {habit_text}", chat_id)
    
    if completed:
        user["habit_streak"] = user.get("habit_streak", 0) + 1
        user["habit_days_left"] = max(0, user.get("habit_days_left", 21) - 1)
        save_user(chat_id, user)
        
        if user["habit_days_left"] == 0:
            return chat_with_ai(f"I just completed my 21-day habit challenge: {user['habit']}! Final streak: {user['habit_streak']} days!", chat_id)
        else:
            return chat_with_ai(f"I completed my habit today: {user['habit']}. Day {user['habit_streak']} done, {user['habit_days_left']} days to go!", chat_id)

def get_available_models():
    """Get list of available models from OpenRouter"""
    available_models = [
        "anthropic/claude-3-haiku",        # Fast, cheap, good for conversations
        "openai/gpt-3.5-turbo",           # Reliable OpenAI model
        "meta-llama/llama-3.1-8b-instruct", # Good open source option
        "google/gemini-flash-1.5",        # Fast Google model
        "mistralai/mistral-7b-instruct"   # Good for specific tasks
    ]
    return available_models

# Test function for OpenRouter
def test_openrouter():
    """Test OpenRouter connection"""
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": "Say 'OpenRouter is working!'"}],
            max_tokens=20
        )
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenRouter Test: {result}")
        return True
    except Exception as e:
        print(f"❌ OpenRouter Test Failed: {e}")
        return False
