# 📥 Installation Guide

## Step-by-Step Setup

### 1. System Requirements

**Required:**
- Python 3.13 or higher
- MySQL 8.0 or higher (or MariaDB 10.x)
- 1GB RAM minimum
- Internet connection

**Operating Systems:**
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS (10.15+)

### 2. Install Python

**Windows:**
Download from python.org
Check installation:
python --version

text

**Linux:**
sudo apt update
sudo apt install python3.13 python3-pip python3-venv

text

### 3. Install MySQL

**Windows:**
Download from mysql.com and install MySQL Server

**Linux:**
sudo apt install mysql-server
sudo mysql_secure_installation

text

Start MySQL:
sudo systemctl start mysql
sudo systemctl enable mysql

text

### 4. Setup Project

Clone or download project
cd AI_Wellwisher_bot

Create virtual environment
python -m venv venv

Activate (Windows)
venv\Scriptsctivate

Activate (Linux/Mac)
source venv/bin/activate

Install dependencies
pip install -r requirements.txt

text

### 5. Configure Environment

Create `.env` file in project root:

Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=soulfriend_bot
DB_PORT=3306

Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=optional_for_future_use

text

### 6. Get API Keys

**Telegram Bot Token:**
1. Open Telegram
2. Search for @BotFather
3. Send /newbot
4. Follow instructions
5. Copy token to .env

**Groq API Key:**
1. Visit console.groq.com
2. Sign up/Login
3. Create API key
4. Copy to .env

### 7. Setup Database

Login to MySQL
mysql -u root -p

Create database
CREATE DATABASE soulfriend_bot;

Verify
SHOW DATABASES;

Exit
EXIT;

text

### 8. Initialize Database Tables

python update_tables.py

text

Expected output:
============================================================
🔧 UPDATING DATABASE TABLES
✅ Database 'soulfriend_bot' ready
📋 Creating users table...
📋 Creating goals table...
...
✅ UPDATE COMPLETE!

text

### 9. Test Bot

python bot.py

text

Expected output:
============================================================
🤖 REGISTERING HANDLERS...
✅ SoulFriend Bot Running!

text

### 10. Test in Telegram

1. Find your bot on Telegram
2. Send /start
3. Complete onboarding
4. Try /addgoal

## Troubleshooting

### MySQL Connection Error
Error: Can't connect to MySQL server

text
**Fix:** Check MySQL is running, verify credentials in .env

### Module Not Found
ModuleNotFoundError: No module named 'telegram'

text
**Fix:** Activate venv and run: pip install -r requirements.txt

### Bot Not Responding
Bot doesn't reply to commands

text
**Fix:** 
1. Check BOT_TOKEN is correct
2. Ensure bot is running
3. Check internet connection

### Database Table Error
Table 'soulfriend_bot.users' doesn't exist

text
**Fix:** Run python update_tables.py

## Next Steps

After successful installation:
1. Set your timezone: /settimezone
2. Create first goal: /addgoal
3. Test reminders
4. Activate premium demo: /activatedemo
5. View charts: /weeklyreport

## Support

Issues? Check:
1. Python version: python --version (need 3.13+)
2. MySQL running: sudo systemctl status mysql
3. .env file exists and has correct values
4. Virtual environment activated

---

**Installation Complete! 🎉**
