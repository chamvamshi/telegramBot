"""
Database Connection - Railway Compatible
"""
import mysql.connector
import os

def get_db_connection():
    """Connect to Railway MySQL"""
    try:
        # Railway MySQL connection
        config = {
            'host': os.getenv('MYSQLHOST', 'localhost'),
            'user': os.getenv('MYSQLUSER', 'root'),
            'password': os.getenv('MYSQLPASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'railway'),
            'port': int(os.getenv('MYSQLPORT', 3306))
        }
        
        conn = mysql.connector.connect(**config)
        return conn
        
    except mysql.connector.Error as e:
        print(f"❌ DB Connection Error: {e}")
        return None

def get_connection():
    """Alias for compatibility"""
    return get_db_connection()
