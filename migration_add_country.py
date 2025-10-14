"""
Add country column to users table
Run this on Railway MySQL
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

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    print("🔧 Adding 'country' column to users table...")
    
    # Check if column exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'country'
    """, (config['database'],))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        print("✅ Column 'country' already exists")
    else:
        cursor.execute("ALTER TABLE users ADD COLUMN country VARCHAR(100) DEFAULT NULL")
        conn.commit()
        print("✅ Added 'country' column to users table")
    
    cursor.close()
    conn.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
