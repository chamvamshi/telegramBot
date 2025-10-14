"""
Complete Database Migration - Fix All Missing Columns
"""
import mysql.connector
import os

config = {
    'host': os.getenv('MYSQLHOST', 'shuttle.proxy.rlwy.net'),
    'port': int(os.getenv('MYSQLPORT', 34292)),
    'user': os.getenv('MYSQLUSER', 'root'),
    'password': os.getenv('MYSQLPASSWORD', 'VNjczVuuZXcCTwUvGBrJwOYOINtxWbah'),
    'database': os.getenv('MYSQL_DATABASE', 'railway')
}

def column_exists(cursor, table, column):
    """Check if column exists in table"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND COLUMN_NAME = %s
    """, (config['database'], table, column))
    return cursor.fetchone()[0] > 0

try:
    print("🔧 Connecting to Railway MySQL...\n")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    migrations = [
        # Add country to users
        {
            'table': 'users',
            'column': 'country',
            'sql': "ALTER TABLE users ADD COLUMN country VARCHAR(100) DEFAULT NULL"
        },
        # Add goal_id to daily_tracking (if that table exists)
        {
            'table': 'daily_tracking',
            'column': 'goal_id',
            'sql': "ALTER TABLE daily_tracking ADD COLUMN goal_id INT DEFAULT NULL"
        },
        # Add habit_id to daily_tracking
        {
            'table': 'daily_tracking',
            'column': 'habit_id',
            'sql': "ALTER TABLE daily_tracking ADD COLUMN habit_id INT DEFAULT NULL"
        }
    ]
    
    for migration in migrations:
        # Check if table exists first
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s
        """, (config['database'], migration['table']))
        
        if cursor.fetchone()[0] == 0:
            print(f"⚠️  Table '{migration['table']}' doesn't exist, skipping...")
            continue
        
        # Check if column exists
        if column_exists(cursor, migration['table'], migration['column']):
            print(f"✅ {migration['table']}.{migration['column']} already exists")
        else:
            print(f"🔧 Adding {migration['table']}.{migration['column']}...")
            cursor.execute(migration['sql'])
            conn.commit()
            print(f"✅ Added {migration['table']}.{migration['column']}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 ALL MIGRATIONS COMPLETE!")
    print("\nYour bot should now work on Railway!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIf you see table not found errors, you may need to:")
    print("1. Check which tables actually exist")
    print("2. Update database/tables.py to create missing tables")
