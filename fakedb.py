import sqlite3
import random
from datetime import datetime, timedelta
import json

# List of sample foods with their base nutrient ranges
SAMPLE_FOODS = [
    {
        'name': 'Upma',
        'calories': (200, 300),
        'nutrients': {
            'Protein': (2.5, 4.5),
            'Carbs': (15, 25),
            'Fat': (0.2, 0.8)
        },
        'micronutrients': {
            'Iron': (0.8, 1.5),
            'Magnesium': (18, 25),
            'Calcium': (100, 140)
        }
    },
    {
        'name': 'Biriyani',
        'calories': (300, 400),
        'nutrients': {
            'Protein': (8, 12),
            'Carbs': (45, 65),
            'Fat': (12, 18)
        },
        'micronutrients': {
            'Iron': (1.5, 2.5),
            'Magnesium': (40, 50),
            'Calcium': (25, 35)
        }
    },
    {
        'name': 'Dosa',
        'calories': (120, 150),
        'nutrients': {
            'Protein': (1.5, 2.5),
            'Carbs': (18, 25),
            'Fat': (1.5, 2.5)
        },
        'micronutrients': {
            'Iron': (1.2, 1.8),
            'Magnesium': (22, 30),
            'Calcium': (8, 12)
        }
    },
    {
        'name': 'Chapati',
        'calories': (100, 140),
        'nutrients': {
            'Protein': (2.5, 3.5),
            'Carbs': (12, 18),
            'Fat': (0.8, 1.2)
        },
        'micronutrients': {
            'Iron': (0.7, 1.1),
            'Magnesium': (18, 24),
            'Calcium': (6, 10)
        }
    },
    {
        'name': 'Fish Curry',
        'calories': (250, 350),
        'nutrients': {
            'Protein': (18, 22),
            'Carbs': (12, 18),
            'Fat': (4, 6)
        },
        'micronutrients': {
            'Iron': (1.8, 2.6),
            'Magnesium': (35, 45),
            'Calcium': (50, 70)
        }
    }
]

def generate_random_entry(date):
    """Generate a random food entry with realistic nutrient values."""
    food = random.choice(SAMPLE_FOODS)
    servings = random.uniform(1.0, 2.0)  # Random servings between 1 and 2
    
    # Generate random values within the specified ranges, adjusted for servings
    calories = round(random.uniform(*food['calories']) * servings, 2)
    
    nutrients = {
        key: round(random.uniform(*ranges) * servings, 2)
        for key, ranges in food['nutrients'].items()
    }
    
    micronutrients = {
        key: round(random.uniform(*ranges) * servings, 2)
        for key, ranges in food['micronutrients'].items()
    }
    
    return {
        'time_uploaded': date.strftime('%Y-%m-%d %H:%M:%S'),
        'food_name': food['name'],
        'calories': calories,
        'nutrients': json.dumps(nutrients),
        'micronutrients': json.dumps(micronutrients)
    }

def create_fake_data():
    """Create a database with fake entries for the past 30 days."""
    # Connect to database
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_uploaded TEXT,
        food_name TEXT,
        calories TEXT,
        nutrients TEXT,
        micronutrients TEXT
    )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM user_info')
    
    # Generate entries for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # For each day, generate 2-4 food entries
    current_date = start_date
    while current_date <= end_date:
        # Generate random number of entries for this day
        num_entries = random.randint(2, 4)
        
        # Generate entries spread throughout the day
        for _ in range(num_entries):
            # Random hour between 7 AM and 9 PM
            entry_hour = random.randint(7, 21)
            entry_minute = random.randint(0, 59)
            entry_date = current_date.replace(hour=entry_hour, minute=entry_minute)
            
            entry = generate_random_entry(entry_date)
            
            cursor.execute('''
            INSERT INTO user_info (time_uploaded, food_name, calories, nutrients, micronutrients)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                entry['time_uploaded'],
                entry['food_name'],
                str(entry['calories']),
                entry['nutrients'],
                entry['micronutrients']
            ))
        
        current_date += timedelta(days=1)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print('Fake data has been generated for the past 30 days!')

if __name__ == '__main__':
    create_fake_data()