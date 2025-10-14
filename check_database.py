
import mysql.connector
import os

config = {
    'host': 'shuttle.proxy.rlwy.net',
    'port': 34292,
    'user': 'root',
    'password': 'VNjczVuuZXcCTwUvGBrJwOYOINtxWbah',
    'database': 'railway'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Get all tables
cursor.execute("SHOW TABLES")
tables = [t[0] for t in cursor.fetchall()]

print("📊 Tables in Railway database:")
for table in tables:
    cursor.execute(f"DESCRIBE {table}")
    columns = [col[0] for col in cursor.fetchall()]
    print(f"\n  {table}:")
    for col in columns:
        print(f"    - {col}")

cursor.close()
conn.close()
