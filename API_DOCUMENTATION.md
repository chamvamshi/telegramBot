# 📡 API Documentation

## Database Functions

### database/user_db.py

#### get_user(chat_id)
Returns user data from database

**Parameters:**
- chat_id (int): Telegram chat ID

**Returns:** dict or None

**Example:**
user = get_user(123456789)
print(user['name']) # "John"

text

#### save_user(chat_id, user_data)
Save/update user data

**Parameters:**
- chat_id (int): Telegram chat ID
- user_data (dict): User information

**Returns:** bool

---

### database/goal_db.py

#### add_goal(chat_id, goal, target_days, motivation, reminder_times)
Create new goal

**Parameters:**
- chat_id (int)
- goal (str): Goal description
- target_days (int): Number of days
- motivation (str): Motivation text
- reminder_times (list): ["09:00", "18:00"]

**Returns:** int (goal_id)

#### get_all_goals(chat_id, status='active')
Get user's goals

**Parameters:**
- chat_id (int)
- status (str): 'active' or 'completed'

**Returns:** list of dicts

#### complete_goal_today(chat_id, goal_id)
Mark goal completed for today

**Parameters:**
- chat_id (int)
- goal_id (int)

**Returns:** dict (updated goal)

---

### database/premium_db.py

#### is_premium_user(chat_id)
Check if user has active premium

**Parameters:**
- chat_id (int)

**Returns:** bool

#### activate_premium(chat_id, subscription_type, payment_id)
Activate premium subscription

**Parameters:**
- chat_id (int)
- subscription_type (str): 'monthly' or 'yearly'
- payment_id (str): Payment reference

**Returns:** bool

#### track_daily_progress(chat_id)
Track today's completion

**Parameters:**
- chat_id (int)

**Returns:** None

#### get_weekly_stats(chat_id, week_offset=0)
Get weekly statistics

**Parameters:**
- chat_id (int)
- week_offset (int): 0=current, -1=last week

**Returns:** dict with completion data

#### award_badge(chat_id, badge_type, completion_rate)
Award achievement badge

**Parameters:**
- chat_id (int)
- badge_type (str): 'soul_silver', 'soul_gold', 'soul_diamond', 'pure_soul'
- completion_rate (float): Percentage

**Returns:** bool

---

## Services

### services/ai_response.py

#### chat_with_ai(prompt, chat_id)
Get AI motivation

**Parameters:**
- prompt (str): Context for AI
- chat_id (int): User ID

**Returns:** str (AI response)

---

### services/chart_generator.py

#### create_weekly_progress_chart(chat_id, weekly_data)
Generate weekly chart

**Parameters:**
- chat_id (int)
- weekly_data (dict): Optional stats

**Returns:** BytesIO (PNG image)

#### create_badge_showcase(badges_earned)
Generate badge display

**Parameters:**
- badges_earned (list): List of badge dicts

**Returns:** BytesIO (PNG image)

---

## Database Schema Reference

### users
- chat_id (BIGINT, PRIMARY KEY)
- name (VARCHAR)
- country (VARCHAR)
- timezone (VARCHAR)
- onboarded (BOOLEAN)
- eod_time (VARCHAR)

### goals
- id (INT, AUTO_INCREMENT)
- chat_id (BIGINT, FOREIGN KEY)
- goal_id (INT)
- goal (TEXT)
- target_days (INT)
- streak (INT)
- status (VARCHAR)
- reminder_times (JSON)

### achievements
- id (INT, AUTO_INCREMENT)
- chat_id (BIGINT, FOREIGN KEY)
- badge_type (VARCHAR)
- badge_name (VARCHAR)
- earned_date (DATE)
- week_number (INT)
- completion_rate (DECIMAL)

---

## Environment Variables

Required in .env:

BOT_TOKEN=your_token
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=soulfriend_bot
DB_PORT=3306
GROQ_API_KEY=your_key

text

---

## Error Handling

All database functions return None or False on error.
Always check return values:

user = get_user(chat_id)
if not user:
# Handle error
return

text
