from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
import time, threading
import twilio.twiml
import sqlite3
import random

app = Flask(__name__)
db_filename = 'acc.db'
count = 0
conn = sqlite3.connect(db_filename, check_same_thread=False)
cursor = conn.cursor()

 
account_sid = "ACb31814cf701c394d4bea1fb2b87c8b2c"
auth_token = "38b85885594ba31c9d06148f2fc6afce"
client = TwilioRestClient(account_sid, auth_token) 
 
 
@app.route("/", methods=['GET', 'POST'])
def start():
    resp = twilio.twiml.Response()
    from_number = request.values.get('From', None)
    msg = request.values.get('Body', None)
    
    
    if msg.startswith('create account '):
        
        name = msg[15:]
        
        query = "select * from accounts where number = ?"
        cursor.execute(query, (from_number,))
        
        if len(cursor.fetchall()) == 0:
            query = "select * from accounts where name = ?"
            cursor.execute(query, (name,))
            if len(cursor.fetchall()) == 0:
                query = "insert into accounts (name, number,ingame,lfg,matchid) values (?,?,0,0,0)"
                conn.execute(query, (name, from_number,))
                conn.commit()
                rmsg = "".join(["Successfully registered as ", name])
                resp.message(rmsg)
            else:
                resp.message("Name exists for another number, please try another one.")
        else:
            query = "select name from accounts where number = ?"
            cursor.execute(query, (from_number,))
            rmsg = "".join(["You already have an account, ", cursor.fetchone()[0]])
            resp.message(rmsg)
    
    elif msg.startswith('start game'):
    
        query = "select * from accounts where number = ?"
        cursor.execute(query, (from_number,))
        
        if len(cursor.fetchall()) != 0:
            message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Begun matchmaking...")
            t = threading.Thread(target=matchmaking, args=(from_number,))
            t.start()
        else:
            resp.message("You don't have an account yet. Please create one by texting us 'create account <username>'; yes, it's that easy!")

    
        
    return str(resp)

def matchmaking(from_number):
    query = "update accounts set lfg = 1 where number = ?"
    conn.execute(query, (from_number,))
    query = "select number from accounts where ingame = 0 and lfg = 1 and number != ?"
    cursor.execute(query, (from_number,))
    rows = cursor.fetchall()
    if len(rows) != 0:
        num= rows[0][0]
        message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Match found! Generating game id...")
        query = "update accounts set lfg = 0, ingame = 1, matchid = ? where number = ?"
        conn.execute(query, (count, from_number,))
        conn.execute(query, (count, num,))
    else:
        for x in range(5):
            foundgame = 0
            time.sleep(2)
            query = "select number from accounts where number = ? and ingame = 1"
            cursor.execute(query, (from_number,))
            if len(cursor.fetchall()) != 0:
                message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Match found! Generating game id...")
                foundgame = 1
                break
        if not foundgame:
            query = "update accounts set lfg = 0 where number = ?"
            conn.execute(query, (from_number,))
            message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Matchmaking failed! Try again next time.")
    conn.commit()
if __name__ == "__main__":
    app.run(debug=True)