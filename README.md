# 🤖 SoulFriend - AI-Powered Goal & Habit Tracking Bot

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)

A feature-rich Telegram bot that helps users track goals and build habits with AI-powered motivation, visual progress charts, and achievement badges.

## ✨ Features

### 🎯 Core Features (Free)
- **Goal Tracking** - Set goals with custom durations, track streaks
- **Habit Building** - 21-day habit challenges
- **Multi-Timezone Support** - All reminders in your local time
- **Smart Reminders** - Multiple custom reminder times
- **EOD Summaries** - Daily progress reports
- **AI Motivation** - Personalized encouragement (Groq AI)

### 💎 Premium Features ($4.99/month)
- **📊 Visual Progress Charts** - Beautiful weekly charts
- **🏆 Achievement Badges** - 4 badges: Silver, Gold, Diamond, Pure Soul
- **Automatic Badge Awarding** - Real-time notifications
- **Advanced Analytics** - Track daily/weekly progress

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MySQL 8.0+
- Telegram Bot Token
- Groq API Key

### Installation

Clone repository
git clone <your-repo-url>
cd AI_Wellwisher_bot

Create virtual environment
python -m venv venv
venv\Scriptsctivate # Windows

Install dependencies
pip install -r requirements.txt

Configure .env file
Add: BOT_TOKEN, DB_PASSWORD, GROQ_API_KEY
Setup database
mysql -u root -p
CREATE DATABASE soulfriend_bot;
EXIT;

Initialize tables
python update_tables.py

Run bot
python bot.py

text

## 📁 Project Structure

AI_Wellwisher_bot/
├── bot.py # Main entry point
├── config.py # Configuration
├── .env # Environment variables
├── requirements.txt # Dependencies
├── database/ # Database layer (8 tables)
├── handlers/ # Command handlers
├── services/ # AI & Charts
└── jobs/ # Background tasks

text

## 🎮 Commands

**Basic:** /start, /menu, /help, /profile, /boost

**Goals:** /goals, /addgoal, /goaldone, /deletegoal

**Habits:** /habits, /addhabit, /habitdone, /deletehabit

**Premium:** /premium, /activatedemo, /weeklyreport, /badges

**Settings:** /seteod, /settimezone

## 🗄️ Database

8 Tables: users, goals, habits, premium_users, achievements, weekly_reports, three_day_feedback, daily_tracking

## 🔧 Technology Stack

- Python 3.13 + python-telegram-bot
- MySQL 8.0
- Groq AI
- matplotlib charts
- pytz timezone support

## 🎨 Key Features

### Multi-Timezone
- Auto-detect from country
- Local time reminders
- Timezone customization

### Badge System
- 🥈 Soul Silver (50%+ weekly)
- 🥇 Soul Gold (80%+ weekly)
- 💎 Soul Diamond (90%+ weekly)
- 👑 Pure Soul (Perfect month)

### Charts
- Weekly progress graphs
- Badge showcases
- Real data visualization

## 🔮 Roadmap

- [ ] AI Psychology Insights
- [ ] 3-Day Pattern Detection
- [ ] Payment Integration
- [ ] Export (PDF/CSV)
- [ ] Web Dashboard
- [ ] Admin Panel

## 💰 Pricing

- Free: All basic features
- Premium: $4.99/month or $49/year

## 🐛 Troubleshooting

**Bot not responding?** Check BOT_TOKEN in .env

**Database error?** Verify MySQL running and credentials

**Charts not working?** Run: pip install matplotlib pillow numpy

## 📄 License

MIT License

## 👤 Author

Your Name - GitHub: @yourusername

---

**Built with ❤️ using Python and Telegram Bot API**



## Development Workflow

1. Pick an issue or create one
2. Fork repository
3. Create feature branch
4. Make changes
5. Test thoroughly
6. Submit PR
7. Address review comments
8. Merge!

## Code Review Process

All PRs require:
- Code review by maintainer
- Passing tests
- Documentation updates
- No merge conflicts

## Questions?

Contact via:
- GitHub Issues
- Telegram: @yourusername
- Email: your.email@example.com

Thank you for contributing! 🙏
''',

    'CHANGELOG.md': '''# 📝 Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-10

### Added
- ✨ Initial release
- 🎯 Goal tracking system
- 🔄 Habit tracking (21-day challenges)
- 🌍 Multi-timezone support
- 🔔 Smart reminder system
- 📊 EOD daily summaries
- 🤖 AI motivation (Groq integration)
- 💎 Premium subscription system
- 🏆 Achievement badge system (4 badges)
- 📈 Visual progress charts (matplotlib)
- 🗄️ MySQL database (8 tables)
- 👤 Professional onboarding flow
- ✏️ Full CRUD operations for goals/habits
- 🎨 Beautiful badge showcase
- 📊 Weekly progress reports
- ⚡ Automatic badge awarding
- 🔐 Premium features with demo mode

### Features
- Complete goal lifecycle management
- Streak tracking
- Custom reminder times
- Timezone auto-detection
- Real-time notifications
- Progress visualization
- Database-backed analytics

### Technical
- Python 3.13+
- python-telegram-bot framework
- MySQL 8.0 database
- Groq AI integration
- matplotlib chart generation
- Modular architecture
- Clean code structure

## [Unreleased]

### Planned
- AI psychology insights
- 3-day pattern detection
- Payment integration (Stripe/Razorpay)
- Export data (PDF/CSV)
- Web dashboard
- Admin panel
- Social sharing
- Referral system

---

**Format:** [Version] - YYYY-MM-DD
''',

    'LICENSE': '''MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''',

    '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Charts
*.png
*.jpg
*.jpeg

# Temp files
*.tmp
*.bak
~*
'''
}

# Create all files

for filename, content in files.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {filename}")

print("\n" + "="*60)
print("🎉 ALL DOCUMENTATION CREATED!")
print("="*60)
print("\nFiles created:")
for filename in files.keys():
    print(f"  ✓ {filename}")

print("\n📚 Your project is now fully documented!")
print("\nYou can:")
print("  1. Share these files in a new thread")
print("  2. Push to GitHub")
print("  3. Use as reference documentation")
print("  4. Share with team members")

exit()

## Development Workflow

1. Pick an issue or create one
2. Fork repository
3. Create feature branch
4. Make changes
5. Test thoroughly
6. Submit PR
7. Address review comments
8. Merge!

## Code Review Process

All PRs require:
- Code review by maintainer
- Passing tests
- Documentation updates
- No merge conflicts

## Questions?

Contact via:
- GitHub Issues
- Telegram: @yourusername
- Email: your.email@example.com

Thank you for contributing! 🙏
''',

    'CHANGELOG.md': '''# 📝 Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-10

### Added
- ✨ Initial release
- 🎯 Goal tracking system
- 🔄 Habit tracking (21-day challenges)
- 🌍 Multi-timezone support
- 🔔 Smart reminder system
- 📊 EOD daily summaries
- 🤖 AI motivation (Groq integration)
- 💎 Premium subscription system
- 🏆 Achievement badge system (4 badges)
- 📈 Visual progress charts (matplotlib)
- 🗄️ MySQL database (8 tables)
- 👤 Professional onboarding flow
- ✏️ Full CRUD operations for goals/habits
- 🎨 Beautiful badge showcase
- 📊 Weekly progress reports
- ⚡ Automatic badge awarding
- 🔐 Premium features with demo mode

### Features
- Complete goal lifecycle management
- Streak tracking
- Custom reminder times
- Timezone auto-detection
- Real-time notifications
- Progress visualization
- Database-backed analytics

### Technical
- Python 3.13+
- python-telegram-bot framework
- MySQL 8.0 database
- Groq AI integration
- matplotlib chart generation
- Modular architecture
- Clean code structure

## [Unreleased]

### Planned
- AI psychology insights
- 3-day pattern detection
- Payment integration (Stripe/Razorpay)
- Export data (PDF/CSV)
- Web dashboard
- Admin panel
- Social sharing
- Referral system

---

**Format:** [Version] - YYYY-MM-DD
''',

    'LICENSE': '''MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''',

    '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Charts
*.png
*.jpg
*.jpeg

# Temp files
*.tmp
*.bak
~*
'''
}

# Create all files
for filename, content in files.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {filename}")

print("\n" + "="*60)
print("🎉 ALL DOCUMENTATION CREATED!")
print("="*60)
print("\nFiles created:")
for filename in files.keys():
    print(f"  ✓ {filename}")

print("\n📚 Your project is now fully documented!")
print("\nYou can:")
print("  1. Share these files in a new thread")
print("  2. Push to GitHub")
print("  3. Use as reference documentation")
print("  4. Share with team members")

exit()
