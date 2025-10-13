
from database.premium_db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

try:
    # Check if table exists and has correct columns
    cursor.execute("""
        SHOW COLUMNS FROM premium_users
    """)
    
    columns = [col[0] for col in cursor.fetchall()]
    print(f"✅ premium_users columns: {columns}")
    
    required = ['chat_id', 'subscription_type', 'is_active', 'start_date', 'end_date']
    missing = [col for col in required if col not in columns]
    
    if missing:
        print(f"⚠️ Missing columns: {missing}")
        print("\nAdding missing columns...")
        
        for col in missing:
            if col == 'subscription_type':
                cursor.execute("ALTER TABLE premium_users ADD COLUMN subscription_type VARCHAR(50) DEFAULT 'trial'")
            elif col == 'is_active':
                cursor.execute("ALTER TABLE premium_users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            elif col == 'start_date':
                cursor.execute("ALTER TABLE premium_users ADD COLUMN start_date DATETIME")
            elif col == 'end_date':
                cursor.execute("ALTER TABLE premium_users ADD COLUMN end_date DATETIME")
        
        conn.commit()
        print("✅ Added missing columns")
    else:
        print("✅ All required columns exist")
        
except Exception as e:
    print(f"Error checking table: {e}")
finally:
    cursor.close()
    conn.close()
