"""
Database Connection Handler - Works on Railway and Local
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection - supports multiple env var formats"""
    try:
        # Support both Railway formats and local
        config = {
            'host': (
                os.getenv('MYSQLHOST') or 
                os.getenv('MYSQL_HOST') or 
                os.getenv('DB_HOST', 'localhost')
            ),
            'user': (
                os.getenv('MYSQLUSER') or 
                os.getenv('MYSQL_USER') or 
                os.getenv('DB_USER', 'root')
            ),
            'password': (
                os.getenv('MYSQLPASSWORD') or 
                os.getenv('MYSQL_PASSWORD') or 
                os.getenv('DB_PASSWORD', '')
            ),
            'database': (
                os.getenv('MYSQLDATABASE') or 
                os.getenv('MYSQL_DATABASE') or 
                os.getenv('DB_NAME', 'railway')
            ),
            'port': int(
                os.getenv('MYSQLPORT') or 
                os.getenv('MYSQL_PORT') or 
                os.getenv('DB_PORT', 3306)
            ),
            'connect_timeout': 10
        }
        
        # Debug log
        print(f"�� Connecting to: {config['host']}:{config['port']} / {config['database']}")
        
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            print(f"✅ Connected to database successfully!")
            return connection
    except Error as e:
        print(f"❌ DB Connection Error: {e}")
        return None

# Backwards compatibility
def get_connection():
    return get_db_connection()
