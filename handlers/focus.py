from telegram import Update
from telegram.ext import ContextTypes

async def focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tips = (
        "🎯 **Focus Tips:**\n\n"
        "• **Pomodoro Technique**: 25 min work, 5 min break\n"
        "• **Minimize distractions**: Phone on silent, close social media\n"
        "• **Set clear goals**: Know what you want to achieve\n"
        "• **Create a dedicated space**: Find your focus zone\n"
        "• **Take regular breaks**: Your brain needs rest too!"
    )
    await update.message.reply_text(tips, parse_mode='Markdown')
