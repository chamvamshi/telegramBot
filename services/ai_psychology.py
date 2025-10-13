"""
AI Psychology Analysis
Uses OpenRouter for advanced psychology insights
"""

from openai import OpenAI
from config import OPENROUTER_API_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_psychology_insights(chat_id, weekly_stats, moods, conversations, user_name):
    """Generate 2-3 line psychological insight using Claude/GPT"""
    
    # Build context
    completion_rate = 0
    if weekly_stats:
        total_completed = (weekly_stats.get('goals_completed') or 0) + (weekly_stats.get('habits_completed') or 0)
        total_tasks = (weekly_stats.get('total_goals') or 0) + (weekly_stats.get('total_habits') or 0)
        completion_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
    
    # Mood analysis
    mood_summary = "No mood data this week"
    mood_trend = "neutral"
    if moods:
        mood_list = [m.get('mood') for m in moods if m.get('mood')]
        energy_avg = sum([m.get('energy_level', 5) for m in moods]) / len(moods) if moods else 5
        
        # Detect trend
        negative_moods = sum(1 for m in mood_list if m in ['lonely', 'sad', 'stressed', 'anxious'])
        positive_moods = sum(1 for m in mood_list if m in ['great', 'good'])
        
        if negative_moods > positive_moods:
            mood_trend = "declining"
        elif positive_moods > negative_moods:
            mood_trend = "improving"
        
        mood_summary = f"Moods: {', '.join(mood_list[-5:])}. Energy: {energy_avg:.1f}/10. Trend: {mood_trend}"
    
    # Emotional concerns detection
    concerns = []
    concern_quotes = []
    if conversations:
        for conv in conversations:
            msg = conv.get('user_message', '').lower()
            if any(word in msg for word in ['lonely', 'alone', 'isolated']):
                concerns.append('loneliness')
                concern_quotes.append(msg[:100])
            if any(word in msg for word in ['stressed', 'overwhelmed', 'pressure']):
                concerns.append('stress')
                concern_quotes.append(msg[:100])
            if any(word in msg for word in ['sad', 'depressed', 'down', 'hopeless']):
                concerns.append('sadness')
                concern_quotes.append(msg[:100])
            if any(word in msg for word in ['anxious', 'worried', 'nervous', 'fear']):
                concerns.append('anxiety')
                concern_quotes.append(msg[:100])
    
    concern_text = f"Emotional concerns: {', '.join(set(concerns))}" if concerns else "No major concerns detected"
    
    # Behavioral patterns
    behavior_pattern = "consistent" if completion_rate > 70 else "inconsistent" if completion_rate > 40 else "struggling"
    
    # Create detailed prompt
    prompt = f"""You are an experienced psychologist specializing in behavioral psychology and emotional wellness. Analyze this week's data and provide a brief, compassionate psychological insight.

**User:** {user_name}
**Completion Rate:** {completion_rate:.1f}%
**Behavior Pattern:** {behavior_pattern}
**{mood_summary}**
**{concern_text}**

{f"**Recent expressions:** {concern_quotes[:2]}" if concern_quotes else ""}

**Task:** Provide a warm, personalized 2-3 sentence psychological insight that:
1. Acknowledges their emotional state if concerns exist
2. Identifies a behavioral pattern (positive or area for growth)
3. Offers one actionable, compassionate suggestion

**Tone:** Empathetic, non-judgmental, encouraging, professional
**Length:** Maximum 3 sentences
**Focus:** Mental health, behavior change, emotional wellness

Psychology Insight:"""

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",  # Best for psychology
            # Alternative: "openai/gpt-4-turbo" or "meta-llama/llama-3.1-70b-instruct"
            messages=[
                {
                    "role": "system", 
                    "content": "You are a compassionate psychologist providing brief, actionable insights based on behavioral data and emotional patterns."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=200,
        )
        
        insight = response.choices[0].message.content.strip()
        
        # Remove any formatting
        insight = insight.replace('**', '').replace('*', '')
        
        return insight
        
    except Exception as e:
        print(f"AI Psychology Error: {e}")
        
        # Fallback based on data
        if concerns:
            if 'loneliness' in concerns:
                return f"{user_name}, feeling alone is valid. Your {completion_rate:.0f}% completion shows you're still showing up for yourself. Consider reaching out to one person today - connection heals."
            elif 'stress' in concerns:
                return f"{user_name}, stress is affecting your progress ({completion_rate:.0f}%). Break tasks into smaller steps. Remember: progress, not perfection."
            elif 'anxiety' in concerns:
                return f"{user_name}, anxiety can be overwhelming. Your {completion_rate:.0f}% shows resilience. Try grounding exercises before tackling goals."
        
        # Generic positive feedback
        if completion_rate >= 70:
            return f"{user_name}, your {completion_rate:.0f}% completion reflects strong discipline. Celebrate these wins - they're building lasting habits."
        elif completion_rate >= 40:
            return f"{user_name}, {completion_rate:.0f}% shows you're making progress despite challenges. Focus on consistency over perfection."
        else:
            return f"{user_name}, starting is brave. Your {completion_rate:.0f}% is a foundation. Set one tiny goal tomorrow - momentum builds gradually."


def analyze_emotional_state(moods, conversations):
    """Detect emotional patterns"""
    
    emotional_state = {
        'primary_emotion': 'neutral',
        'concerns': [],
        'risk_level': 'low'
    }
    
    # Mood analysis
    if moods:
        negative_count = sum(1 for m in moods if m.get('mood') in ['lonely', 'sad', 'stressed', 'anxious'])
        if negative_count >= 4:  # 4+ days of negative mood
            emotional_state['risk_level'] = 'moderate'
            emotional_state['primary_emotion'] = moods[0].get('mood', 'neutral')
    
    # Conversation analysis
    if conversations:
        for conv in conversations:
            msg = conv.get('user_message', '').lower()
            
            # Crisis keywords (very serious)
            if any(word in msg for word in ['suicide', 'kill myself', 'want to die', 'end it all']):
                emotional_state['risk_level'] = 'high'
                emotional_state['concerns'].append('crisis')
            
            # Severe distress
            if any(word in msg for word in ['hopeless', 'worthless', 'no point', 'give up']):
                if emotional_state['risk_level'] != 'high':
                    emotional_state['risk_level'] = 'moderate'
                emotional_state['concerns'].append('severe_distress')
    
    return emotional_state
