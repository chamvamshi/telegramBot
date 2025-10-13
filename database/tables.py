"""
Database Tables Module
All table creation SQL
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 3306))
}

DB_NAME = os.getenv('DB_NAME', 'soulfriend_bot')

def init_all_tables():
    """Create database and all tables"""
    print("\n" + "=" * 70)
    print("🔧 INITIALIZING DATABASE")
    print("=" * 70)
    
    # Create database if not exists
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"✅ Database '{DB_NAME}' ready")
        cursor.close()
        connection.close()
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    # Create tables
    connection = mysql.connector.connect(**{**DB_CONFIG, 'database': DB_NAME})
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Users table
        print("📋 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                country VARCHAR(100),
                timezone VARCHAR(50) DEFAULT 'UTC',
                onboarded BOOLEAN DEFAULT FALSE,
                eod_time VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Goals table
        print("📋 Creating goals table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                goal_id INT NOT NULL,
                goal TEXT NOT NULL,
                target_days INT DEFAULT 30,
                streak INT DEFAULT 0,
                start_date DATE,
                motivation TEXT,
                last_checkin DATE,
                status VARCHAR(20) DEFAULT 'active',
                reminder_times JSON,
                completed_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_goal (chat_id, goal_id),
                INDEX idx_status (chat_id, status)
            )
        """)
        
        # Habits table
        print("📋 Creating habits table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                habit_id INT NOT NULL,
                habit TEXT NOT NULL,
                days_target INT DEFAULT 21,
                streak INT DEFAULT 0,
                start_date DATE,
                reminder_times JSON,
                last_completed DATE,
                status VARCHAR(20) DEFAULT 'active',
                completed_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_habit (chat_id, habit_id),
                INDEX idx_status (chat_id, status)
            )
        """)
        
        # Premium users table
        print("📋 Creating premium_users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS premium_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                subscription_type VARCHAR(20) DEFAULT 'monthly',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                payment_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                INDEX idx_active (chat_id, is_active)
            )
        """)
        
        # Achievements table
        print("📋 Creating achievements table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                badge_type VARCHAR(50) NOT NULL,
                badge_name VARCHAR(100) NOT NULL,
                earned_date DATE NOT NULL,
                week_number INT,
                month_number INT,
                year INT,
                completion_rate DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                UNIQUE KEY unique_weekly_badge (chat_id, week_number, year, badge_type)
            )
        """)
        
        # Weekly reports table
        print("📋 Creating weekly_reports table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                week_number INT NOT NULL,
                year INT NOT NULL,
                total_goals INT DEFAULT 0,
                completed_goals INT DEFAULT 0,
                total_habits INT DEFAULT 0,
                completed_habits INT DEFAULT 0,
                completion_rate DECIMAL(5,2),
                ai_analysis TEXT,
                ai_advice TEXT,
                report_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                UNIQUE KEY unique_weekly_report (chat_id, week_number, year)
            )
        """)
        
        # 3-day feedback table
        print("📋 Creating three_day_feedback table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS three_day_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                goal_id INT,
                habit_id INT,
                pattern_detected VARCHAR(255),
                feedback_message TEXT,
                sent_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                INDEX idx_sent_date (chat_id, sent_date)
            )
        """)
        
        # Daily tracking table
        print("📋 Creating daily_tracking table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_tracking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                track_date DATE NOT NULL,
                goals_completed INT DEFAULT 0,
                habits_completed INT DEFAULT 0,
                total_goals INT DEFAULT 0,
                total_habits INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                UNIQUE KEY unique_daily_track (chat_id, track_date)
            )
        """)
        
        connection.commit()
        print("\n" + "=" * 70)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70 + "\n")
        return True
        
    except Error as e:
        print(f"❌ Error creating tables: {e}")
        return False
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("Testing database connection...")
    from .connection import test_connection
    if test_connection():
        init_all_tables()
