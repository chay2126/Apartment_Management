import sqlite3
import sys

conn = sqlite3.connect("apartment.db")
cursor = conn.cursor()

if len(sys.argv) != 2:
    print("Usage: cmd_apartment_payment_total_amount.py <month>")
    sys.exit(1)

month = sys.argv[1]

cursor.execute("SELECT SUM(amount) AS collected_amount FROM payments WHERE month = ? AND status = 'PAID'",(month,))
print(cursor.fetchall())
cursor.close()
conn.close()
