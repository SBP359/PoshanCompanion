import sqlite3

# Create a new SQLite database file
conn = sqlite3.connect("user_data.db")

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create a table to store user information, including micronutrients
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_uploaded TEXT,
        food_name TEXT,
        calories TEXT,
        nutrients TEXT,
        micronutrients TEXT
    )
    """
)

# Commit the changes and close the connection
conn.commit()
conn.close()