
"""
Complete Database Setup Script - Run this to create ALL tables
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Railway MySQL connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

print("🔗 Connecting to Railway MySQL...")
print(f"Host: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected to database\n")
    
    # Create all tables
    tables = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                username VARCHAR(255),
                timezone VARCHAR(100) DEFAULT 'Asia/Kolkata',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """,
        
        'goals': """
            CREATE TABLE IF NOT EXISTS goals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                target_date DATE,
                status VARCHAR(50) DEFAULT 'active',
                progress INT DEFAULT 0,
                reminder_time TIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_chat_id (chat_id),
                INDEX idx_status (status)
            )
        """,
        
        'habits': """
            CREATE TABLE IF NOT EXISTS habits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                frequency VARCHAR(50) DEFAULT 'daily',
                reminder_time TIME,
                status VARCHAR(50) DEFAULT 'active',
                streak INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_chat_id (chat_id),
                INDEX idx_status (status)
            )
        """,
        
        'habit_logs': """
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                habit_id INT NOT NULL,
                chat_id BIGINT NOT NULL,
                completed BOOLEAN DEFAULT TRUE,
                log_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                INDEX idx_habit_date (habit_id, log_date),
                INDEX idx_chat_id (chat_id)
            )
        """,
        
        'mood_tracking': """
            CREATE TABLE IF NOT EXISTS mood_tracking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                track_date DATE NOT NULL,
                mood VARCHAR(50),
                feeling_notes TEXT,
                energy_level INT DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_date (chat_id, track_date)
            )
        """,
        
        'premium_users': """
            CREATE TABLE IF NOT EXISTS premium_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL UNIQUE,
                subscription_type VARCHAR(50) DEFAULT 'trial',
                is_active BOOLEAN DEFAULT TRUE,
                start_date DATETIME,
                end_date DATETIME,
                payment_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cancelled_at TIMESTAMP NULL,
                INDEX idx_chat_id (chat_id),
                INDEX idx_active (is_active)
            )
        """,
        
        'premium_subscriptions': """
            CREATE TABLE IF NOT EXISTS premium_subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                plan_type VARCHAR(50),
                amount DECIMAL(10,2),
                is_active BOOLEAN DEFAULT TRUE,
                subscription_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_id (chat_id)
            )
        """
    }
    
    # Create each table
    for table_name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            conn.commit()
            print(f"✅ Created table: {table_name}")
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")
    
    # Verify tables
    cursor.execute("SHOW TABLES")
    all_tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\n📊 Total tables in database: {len(all_tables)}")
    print(f"Tables: {', '.join(all_tables)}")
    
    print("\n✅ DATABASE SETUP COMPLETE!")
    
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("\nCheck your .env file has:")
    print("  DB_HOST=<railway_host>")
    print("  DB_USER=root")
    print("  DB_PASSWORD=<password>")
    print("  DB_NAME=soulfriend_bot")
    print("  DB_PORT=3306")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
