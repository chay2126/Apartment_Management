import sqlite3
import sys

conn = sqlite3.connect("apartment.db")
cursor = conn.cursor()
if len(sys.argv) != 2:
    print("Usage: python3 cmd_apartment_expense.py <month>")
    sys.exit(1)
month = sys.argv[1]
cursor.execute("Select month, SUM(amount) AS total_spent from expenses where month = ?",(month,))
print(cursor.fetchall())
cursor.close()
conn.close()
