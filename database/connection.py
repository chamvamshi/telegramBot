"""
Database Connection Module
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
    'database': os.getenv('DB_NAME', 'soulfriend_bot'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"❌ DB Connection Error: {e}")
        return None

def test_connection():
    """Test database connection"""
    connection = get_db_connection()
    if connection and connection.is_connected():
        print(f"✅ Connected to MySQL: {connection.get_server_info()}")
        connection.close()
        return True
    print("❌ Connection failed!")
    return False
