import sqlite3

conn = sqlite3.connect('failures.db')
c = conn.cursor()

# Get column info
c.execute("PRAGMA table_info(analyses)")
columns = c.fetchall()

print("\nCurrent database schema:")
print("-" * 50)
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
