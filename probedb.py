import os
import sqlite3

db_filename = 'acc.db'
schema_filename = 'acc_schema.sql'

db_is_new = not os.path.exists(db_filename)

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()
cursor.execute("select * from accounts")
    
for row in cursor.fetchall():
    print row
        
cursor.execute("select * from gsessions")

for row in cursor.fetchall():
    print row