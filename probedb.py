import os
import sqlite3

db_filename = 'acc.db'
schema_filename = 'acc_schema.sql'

db_is_new = not os.path.exists(db_filename)

with sqlite3.connect(db_filename) as conn:
    cursor = conn.cursor()
    cursor.execute("select * from accounts")
    
    for row in cursor.fetchall():
        print row