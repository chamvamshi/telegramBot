"""
Beautiful Progress Chart Generator
NOW WITH REAL DATA!
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, date
import io

plt.style.use('seaborn-v0_8-darkgrid')

def create_weekly_progress_chart(chat_id, weekly_data=None):
    """Create weekly progress chart with REAL DATA"""
    
    # Get real data from database
    from database.premium_db import get_db_connection
    
    connection = get_db_connection()
    if not connection:
        # Fallback to sample data
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        completions = [1, 2, 2, 3, 3, 4, 4]
    else:
        cursor = connection.cursor(dictionary=True, buffered=True)
        
        # Get last 7 days data
        today = date.today()
        seven_days_ago = today - timedelta(days=6)
        
        cursor.execute("""
            SELECT track_date, (goals_completed + habits_completed) as total_completed
            FROM daily_tracking
            WHERE chat_id = %s AND track_date BETWEEN %s AND %s
            ORDER BY track_date
        """, (chat_id, seven_days_ago, today))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        if results and len(results) > 0:
            # Use real data
            days = [r['track_date'].strftime('%a') for r in results]
            completions = [r['total_completed'] for r in results]
            
            # Fill missing days with 0
            while len(days) < 7:
                days.append(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][len(days)])
                completions.append(0)
        else:
            # No data yet - use sample
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            completions = [0, 0, 0, 0, 0, 0, 0]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    
    # Plot
    x = np.arange(len(days))
    ax.plot(x, completions, color='#4A90E2', linewidth=3, marker='o', 
            markersize=10, markerfacecolor='#4A90E2', markeredgewidth=2, markeredgecolor='white')
    ax.fill_between(x, completions, alpha=0.3, color='#4A90E2')
    
    # Styling
    ax.set_xlabel('Day of Week', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Tasks Completed', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Weekly Progress', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(days, fontsize=10)
    ax.set_ylim(bottom=0, top=max(completions) + 1 if max(completions) > 0 else 5)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_facecolor('#fafafa')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Stats
    total = sum(completions)
    avg = total / len(days) if days else 0
    stats_text = f"Total: {total} tasks | Avg: {avg:.1f}/day"
    ax.text(0.5, -0.15, stats_text, ha='center', va='center',
            transform=ax.transAxes, fontsize=11, color='#666',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', edgecolor='none'))
    
    # Trend
    if len(completions) >= 2:
        trend = completions[-1] - completions[0]
        if trend > 0:
            message = f"You are improving! +{trend} tasks"
            color = '#27AE60'
        elif trend < 0:
            message = "Keep pushing!"
            color = '#E74C3C'
        else:
            message = "Steady progress!"
            color = '#4A90E2'
    else:
        message = "Start tracking to see progress!"
        color = '#4A90E2'
    
    ax.text(0.5, 1.05, message, ha='center', va='bottom',
            transform=ax.transAxes, fontsize=12, fontweight='bold', color=color)
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()
    
    return buf

def create_badge_showcase(badges_earned):
    """Create badge showcase with REAL EARNED BADGES"""
    
    fig = plt.figure(figsize=(10, 6), facecolor='white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    fig.suptitle('Your Achievements', fontsize=22, fontweight='bold', y=0.95)
    
    badge_emojis = {
        'soul_silver': '🥈',
        'soul_gold': '🥇',
        'soul_diamond': '💎',
        'pure_soul': '👑'
    }
    
    badge_names = {
        'soul_silver': 'Soul Silver\\n50%+ Weekly',
        'soul_gold': 'Soul Gold\\n80%+ Weekly',
        'soul_diamond': 'Soul Diamond\\n90%+ Weekly',
        'pure_soul': 'Pure Soul\\nPerfect Month'
    }
    
    # Get earned badge types
    earned_types = {b.get('badge_type') for b in badges_earned} if badges_earned else set()
    
    positions = [(0.25, 0.6), (0.75, 0.6), (0.25, 0.3), (0.75, 0.3)]
    badge_order = ['soul_silver', 'soul_gold', 'soul_diamond', 'pure_soul']
    
    for i, badge_type in enumerate(badge_order):
        x, y = positions[i]
        emoji = badge_emojis[badge_type]
        name = badge_names[badge_type]
        
        is_earned = badge_type in earned_types
        
        if is_earned:
            # Show colored badge
            ax.text(x, y, emoji, fontsize=60, ha='center', va='center')
            ax.text(x, y - 0.12, name, fontsize=11, ha='center', va='top',
                   fontweight='bold', color='#333')
            
            # Count
            count = sum(1 for b in badges_earned if b.get('badge_type') == badge_type)
            if count > 1:
                ax.text(x + 0.08, y + 0.08, f'×{count}', fontsize=10, ha='center', va='center',
                       bbox=dict(boxstyle='circle', facecolor='#4A90E2', edgecolor='none'),
                       color='white', fontweight='bold')
        else:
            # Locked
            ax.text(x, y, '🔒', fontsize=50, ha='center', va='center', alpha=0.3)
            ax.text(x, y - 0.12, name, fontsize=11, ha='center', va='top',
                   color='#999', alpha=0.5)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # Message
    if len(earned_types) == 4:
        message = "You've unlocked all badges!"
    elif len(earned_types) > 0:
        message = f"{len(earned_types)}/4 unlocked! Keep going!"
    else:
        message = "Complete goals to unlock badges!"
    
    ax.text(0.5, 0.05, message, ha='center', va='center',
           fontsize=12, fontweight='bold', color='#4A90E2')
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()
    
    return buf
