# soulfriend_bot/services/advice_service.py

import random

# Predefined motivational tips / quotes
ADVICE_LIST = [
    "Believe in yourself and all that you are.",
    "Every day is a new beginning.",
    "Small steps every day lead to big results.",
    "Focus on progress, not perfection.",
    "Your habits shape your future.",
    "Stay positive, work hard, make it happen.",
    "Mindfulness is the key to inner peace.",
    "Embrace challenges—they help you grow."
]

def get_random_advice():
    return random.choice(ADVICE_LIST)
