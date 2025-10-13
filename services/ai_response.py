"""
AI Response Service - Helpful Friend Mode
Uses OpenRouter for practical, empathetic, solution-oriented responses
"""

from openai import OpenAI
from config import OPENROUTER_API_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def chat_with_ai(prompt, chat_id):
    """Get helpful, practical AI response"""
    
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful, caring friend. NOT a therapist.

YOUR PERSONALITY:
- Talk like a real friend, not a counselor
- Give PRACTICAL solutions when asked
- Be warm, casual, and supportive
- Use natural language, not clinical terms
- Provide specific steps/advice when needed
- Don't just validate - actually HELP

WHEN USER ASKS FOR HELP:
✅ Give clear, actionable steps
✅ Share practical tips
✅ Suggest concrete solutions
✅ Be specific and useful

AVOID:
❌ "I hear you" without helping
❌ Just asking more questions
❌ Being overly formal
❌ Therapy-speak

RESPOND LIKE:
"Here are 3 things that might help..." 
"Try this approach..."
"I'd suggest..."

Keep responses 2-4 sentences unless giving steps."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=250,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm here for you. Tell me more about what you need help with."
