"""
Database Connection Handler - Supports Both Local and Railway
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection - works for both local and Railway"""
    try:
        # Try Railway variables first
        config = {
            'host': os.getenv('MYSQLHOST') or os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('MYSQLUSER') or os.getenv('DB_USER', 'root'),
            'password': os.getenv('MYSQLPASSWORD') or os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('MYSQLDATABASE') or os.getenv('DB_NAME', 'soulfriend_bot'),
            'port': int(os.getenv('MYSQLPORT') or os.getenv('DB_PORT', 3306))
        }
        
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None
