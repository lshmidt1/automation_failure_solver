import sqlite3

print("Updating database schema...")

conn = sqlite3.connect('failures.db')
c = conn.cursor()

# Check if columns exist and add them if missing
columns_to_add = [
    ('report_file', 'TEXT'),
    ('test_name', 'TEXT'),
    ('error_message', 'TEXT'),
    ('stack_trace', 'TEXT')
]

for column_name, column_type in columns_to_add:
    try:
        c.execute(f'ALTER TABLE analyses ADD COLUMN {column_name} {column_type}')
        print(f"✅ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print(f"⚠️  Column {column_name} already exists")
        else:
            print(f"❌ Error adding {column_name}: {e}")

conn.commit()
conn.close()

print("✅ Database update complete!")
