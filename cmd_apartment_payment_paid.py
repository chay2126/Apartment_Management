import sqlite3
import sys

conn = sqlite3.connect("apartment.db")
cursor = conn.cursor()

if len(sys.argv) != 2:
    print("Usage: python3 cmd_apartment_payment_paid.py <month>")
    sys.exit(1)

month = sys.argv[1]

cursor.execute("SELECT flat_id, paid_date, payment_mode FROM payments WHERE month = ? AND status = 'PAID'",(month,))

print(cursor.fetchall())
cursor.close()
conn.close()
