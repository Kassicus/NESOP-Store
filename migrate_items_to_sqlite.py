import sqlite3
import csv

conn = sqlite3.connect('nesop_store.db')
c = conn.cursor()

# Create the items table
c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item TEXT PRIMARY KEY,
        description TEXT,
        price REAL
    )
''')

# Optional: Import from CSV if you still have it
try:
    with open('data/items.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            c.execute(
                'INSERT OR IGNORE INTO items (item, description, price) VALUES (?, ?, ?)',
                (row['item'], row['description'], float(row['price']))
            )
except FileNotFoundError:
    print("No items.csv found, just creating the table.")

# Add image column if it doesn't exist
try:
    c.execute('ALTER TABLE items ADD COLUMN image TEXT')
    print("Added 'image' column to items table.")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("'image' column already exists.")
    else:
        raise

conn.commit()
conn.close()
print("Items table created and populated (if CSV was present).")