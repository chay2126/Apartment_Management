import sqlite3
import sys

conn = sqlite3.connect("apartment.db")
cursor = conn.cursor()

if len(sys.argv) != 2:
    print("Usage: cmd_apartment_flat_floor.py <floor_no>")
    sys.exit(1)

floor_no = sys.argv[1]

cursor.execute("Select flat_id, flat_no from flats where floor_no = ?",(floor_no,))
print(cursor.fetchall())
cursor.close()
conn.close()
