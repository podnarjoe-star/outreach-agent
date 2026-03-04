import os
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )

def init_db():
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