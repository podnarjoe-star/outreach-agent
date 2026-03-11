import os
import mysql.connector
from mysql.connector import Error

def get_db():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=int(os.environ.get("MYSQLPORT", 3306))
        )
        return connection
    except Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

def init_db():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                website VARCHAR(255),
                email VARCHAR(255),
                type VARCHAR(255),
                status VARCHAR(50) DEFAULT 'contacted',
                date_first_contacted DATE,
                date_last_contacted DATE,
                followup_due DATE,
                outreach_count INT DEFAULT 1,
                notes TEXT
            )
        """)
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")