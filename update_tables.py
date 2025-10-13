"""
Database Update Script
Adds new premium tables to existing database
"""

from database.tables import init_all_tables
from database.connection import test_connection

def update_database():
    """Update database with new premium tables"""
    
    print("\n" + "=" * 60)
    print("🔧 UPDATING DATABASE TABLES")
    print("=" * 60)
    
    # Test connection first
    print("\n1️⃣ Testing database connection...")
    if not test_connection():
        print("❌ Connection failed! Check your .env file.")
        return False
    
    # Update tables
    print("\n2️⃣ Adding premium tables...")
    if init_all_tables():
        print("\n✅ Database updated successfully!")
        print("\n📋 New tables added:")
        print("   • premium_users - Subscription management")
        print("   • achievements - Badge system")
        print("   • weekly_reports - Weekly analytics")
        print("   • three_day_feedback - Pattern detection")
        print("   • daily_tracking - Progress tracking")
        
        # Verify tables
        print("\n3️⃣ Verifying tables...")
        from database.connection import get_db_connection
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print("\n📊 All tables in database:")
            for table in tables:
                print(f"   ✓ {table[0]}")
            
            cursor.close()
            connection.close()
        
        print("\n" + "=" * 60)
        print("✅ UPDATE COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python bot.py")
        print("2. Test premium: /activatedemo")
        print("3. Check report: /weeklyreport")
        print("=" * 60 + "\n")
        
        return True
    else:
        print("\n❌ Failed to update database!")
        return False

if __name__ == "__main__":
    update_database()
