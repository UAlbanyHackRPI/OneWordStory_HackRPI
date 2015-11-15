import os
import sqlite3

db_filename = 'acc.db'
schema_filename = 'acc_schema.sql'

db_is_new = not os.path.exists(db_filename)

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()
    
conn.execute("""
    drop table accounts
    """)

conn.execute("""
    drop table gsessions
    """)

conn.execute("""
    create table accounts(
    name text UNIQUE,
    number text UNIQUE,
    ingame integer,
    lfg integer,
    matchid integer,
    userid integer PRIMARY KEY
    );
    """);

conn.execute("""
    insert into accounts (name, number, ingame, lfg, matchid) values ('tfrometa0221', '+13476146825', 0, 0, 0)
    """)

conn.execute("""
    insert into accounts (name, number, ingame, lfg, matchid) values ('KounRyuSui', '+15184951131', 0, 0, 0)
    """)    

conn.execute("""
    create table gsessions(
    matchid integer,
    turn integer,
    name1 integer,
    name2 integer,
    story text
    );
    """);

cursor.execute("select * from accounts")
    
for row in cursor.fetchall():
    print row
    
cursor.execute("select * from gsessions")

for row in cursor.fetchall():
    print row