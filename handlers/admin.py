
"""
Admin Dashboard - Monitor Bot Usage
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.premium_db import get_db_connection
from datetime import datetime, timedelta

# YOUR ADMIN CHAT ID - Replace with your Telegram chat ID
ADMIN_CHAT_ID = 1038137211  # Your chat_id

def is_admin(chat_id):
    """Check if user is admin"""
    return chat_id == ADMIN_CHAT_ID

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics - Admin only"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Unauthorized. Admin only.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total users
        cursor.execute("SELECT COUNT(DISTINCT chat_id) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users today
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(DISTINCT chat_id) as today 
            FROM users 
            WHERE DATE(created_at) = %s
        """, (today,))
        users_today = cursor.fetchone()['today']
        
        # Total goals
        cursor.execute("SELECT COUNT(*) as total FROM goals")
        total_goals = cursor.fetchone()['total']
        
        # Active goals
        cursor.execute("SELECT COUNT(*) as active FROM goals WHERE status = 'active'")
        active_goals = cursor.fetchone()['active']
        
        # Total habits
        cursor.execute("SELECT COUNT(*) as total FROM habits")
        total_habits = cursor.fetchone()['total']
        
        # Active habits
        cursor.execute("SELECT COUNT(*) as active FROM habits WHERE status = 'active'")
        active_habits = cursor.fetchone()['active']
        
        # Mood checks today
        try:
            cursor.execute("""
                SELECT COUNT(*) as today 
                FROM mood_tracking 
                WHERE DATE(track_date) = %s
            """, (today,))
            mood_today = cursor.fetchone()['today']
        except:
            mood_today = 0
        
        # Premium users
        cursor.execute("""
            SELECT COUNT(*) as premium 
            FROM premium_users 
            WHERE is_active = TRUE
        """)
        premium_users = cursor.fetchone()['premium']
        
        # Trial users
        cursor.execute("""
            SELECT COUNT(*) as trial 
            FROM premium_users 
            WHERE is_active = TRUE AND subscription_type = 'trial'
        """)
        trial_users = cursor.fetchone()['trial']
        
        # Build stats message
        message = (
            f"📊 **Admin Dashboard**\n"
            f"_Last updated: {datetime.now().strftime('%I:%M %p')}_ \n\n"
            f"👥 **USERS**\n"
            f"• Total Users: **{total_users}**\n"
            f"• New Today: **{users_today}**\n"
            f"• Premium: **{premium_users}** ({trial_users} on trial)\n\n"
            f"🎯 **GOALS**\n"
            f"• Total Created: **{total_goals}**\n"
            f"• Active Now: **{active_goals}**\n\n"
            f"🔥 **HABITS**\n"
            f"• Total Created: **{total_habits}**\n"
            f"• Active Now: **{active_habits}**\n\n"
            f"💭 **MOOD TRACKING**\n"
            f"• Check-ins Today: **{mood_today}**\n\n"
            f"Use /adminusers to see user list"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    finally:
        cursor.close()
        conn.close()


async def admin_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users - Admin only"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Unauthorized. Admin only.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get recent users
        cursor.execute("""
            SELECT u.chat_id, u.name, u.created_at,
                   (SELECT COUNT(*) FROM goals WHERE chat_id = u.chat_id) as goals,
                   (SELECT COUNT(*) FROM habits WHERE chat_id = u.chat_id) as habits,
                   (SELECT is_active FROM premium_users WHERE chat_id = u.chat_id LIMIT 1) as is_premium
            FROM users u
            ORDER BY u.created_at DESC
            LIMIT 20
        """)
        
        users = cursor.fetchall()
        
        if not users:
            await update.message.reply_text("No users yet.")
            return
        
        message = "👥 **Recent Users** (Last 20)\n\n"
        
        for user in users:
            name = user['name'] or 'Anonymous'
            premium_badge = '💎' if user.get('is_premium') else ''
            message += (
                f"{premium_badge} **{name}**\n"
                f"  ID: `{user['chat_id']}`\n"
                f"  Goals: {user['goals']} | Habits: {user['habits']}\n"
                f"  Joined: {user['created_at'].strftime('%b %d')}\n\n"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    finally:
        cursor.close()
        conn.close()


async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users - Admin only"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Unauthorized. Admin only.")
        return
    
    # Get message to broadcast
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Usage: `/adminbroadcast Your message here`\n\n"
            "This will send your message to ALL users.\n"
            "Use carefully!",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all user chat_ids
        cursor.execute("SELECT DISTINCT chat_id FROM users")
        users = cursor.fetchall()
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['chat_id'],
                    text=f"📢 **Announcement**\n\n{message_text}",
                    parse_mode='Markdown'
                )
                sent += 1
            except:
                failed += 1
        
        await update.message.reply_text(
            f"✅ **Broadcast Complete**\n\n"
            f"Sent: {sent}\n"
            f"Failed: {failed}",
            parse_mode='Markdown'
        )
    
    finally:
        cursor.close()
        conn.close()
