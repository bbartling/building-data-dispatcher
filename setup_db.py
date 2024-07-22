import sqlite3

def setup_database():
    conn = sqlite3.connect('bacnet_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bacnet_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_instance INTEGER NOT NULL,
            object_identifier TEXT NOT NULL,
            property_identifier TEXT NOT NULL,
            value REAL,
            description TEXT,
            brick_class TEXT,
            timestamp TEXT,
            location TEXT,
            device_brick_class TEXT,
            feeds TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    print("Database setup complete.")
