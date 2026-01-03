import sqlite3
import sys

conn = sqlite3.connect("apartment.db")
cursor = conn.cursor()


if len(sys.argv) != 2:
    print("Usage: python3 cmd_apartment_payment_due.py <month>")
    sys.exit(1)
month = sys.argv[1]

cursor.execute("SELECT flat_id FROM payments WHERE month = ? AND status = 'DUE'",(month,))
print(cursor.fetchall())
cursor.close()
conn.close()    
