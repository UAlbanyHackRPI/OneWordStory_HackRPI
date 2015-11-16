from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
import time, threading
import twilio.twiml
import sqlite3
import random

app = Flask(__name__)
db_filename = 'acc.db'
ctfile = open('count.txt', "r+")
count = int(ctfile.read())
ctfile.close()
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
    
    
    if msg.lower().startswith('create account '):
        
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
    
    elif msg.lower().startswith('delete account'):
        query = "select matchid from accounts where number = ?"
        cursor.execute(query, (from_number,))
        matchid = cursor.fetchall()[0][0]
        
        if matchid != 0:
            resp.message("You're currently in a game! Don't ragequit like that!")
            return str(resp)
    
        conn.execute("delete from accounts where number = ?", (from_number,))
        resp.message("Account has been deleted.")
    
    elif msg.lower().startswith('start game'):
    
        query = "select * from accounts where number = ?"
        cursor.execute(query, (from_number,))
        
        rows = cursor.fetchall()
        matchid = rows[0][4]
        
        if matchid != 0:
            resp.message("You're already in a game!")
            return str(resp)
        
        if len(rows) != 0:
            message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Begun matchmaking...")
            t = threading.Thread(target=matchmaking, args=(from_number,))
            t.start()
        else:
            resp.message("You don't have an account yet. Please create one by texting us 'create account <username>'; yes, it's that easy!")
    
    elif msg.lower().startswith('opt out'):
        query = "select matchid from accounts where number = ?"
        cursor.execute(query, (from_number,))
        matchid = cursor.fetchall()[0][0]
        
        if matchid == 0:
            resp.message("You're not in a game!")
            return str(resp)
        
        query = "select name1, name2 from gsessions where matchid = ?"
        cursor.execute(query, (matchid,))
        
        names = cursor.fetchall()[0]
        
        cursor.execute("select number from accounts where matchid = ?", (matchid,))
        
        nums = []
        for row in cursor.fetchall():
            nums.append(row)
        msg = "".join(["Story has been opted out of and saved to db #", str(matchid)])
        query = "update accounts set ingame = 0, matchid = 0 where name = ? or name = ?"
        conn.execute(query, (names[0], names[1],))
        message = client.messages.create(to=nums[0], from_="+15183124106",
                                     body=msg)
        message = client.messages.create(to=nums[1], from_="+15183124106",
                                     body=msg)
                                     
        query = "select story from gsessions where matchid = ?"
        cursor.execute(query, (matchid,))
        msg = "".join(["Your story: ", cursor.fetchall()[0][0]])
        message = client.messages.create(to=nums[0], from_="+15183124106",
                                     body=msg)
        message = client.messages.create(to=nums[1], from_="+15183124106",
                                     body=msg)
        conn.commit()
    
    else:
        """assumed to be a word entry for the story"""
        
        msg = msg.split()[0]
        query = "select accounts.name, gsessions.matchid, gsessions.turn from accounts,gsessions where accounts.name = gsessions.name1"
        cursor.execute(query)
        for row in cursor.fetchall():
            name, matchid, turn = row
        cursor.execute("select name from accounts where number = ?", (from_number,))
        if (turn % 2 == 0) and (name == cursor.fetchall()[0][0]):
            query = "select story from gsessions where matchid = ?"
            cursor.execute(query, (matchid,))
            story = cursor.fetchall()[0][0]
            story += msg
            story += " "
            query = "update gsessions set story = ?, turn = (turn+1) where matchid = ?"
            conn.execute(query, (story, matchid,))
            cursor.execute("select accounts.name from accounts,gsessions where accounts.name = gsessions.name2 and gsessions.matchid = ?", (matchid,))
            name_to = cursor.fetchall()[0][0]
            print name_to
            cursor.execute("select number from accounts where name = ?", (name_to,))
            to_number = cursor.fetchall()[0][0]
            message = client.messages.create(to=to_number, from_="+15183124106",
                                     body=msg)
            conn.commit()
        elif (turn % 2 == 1) and (name != cursor.fetchall()[0][0]): 
            query = "select story from gsessions where matchid = ?"
            cursor.execute(query, (matchid,))
            story = cursor.fetchall()[0][0]
            story += msg
            story += " "
            query = "update gsessions set story = ?, turn = (turn+1) where matchid = ?"
            conn.execute(query, (story, matchid,))
            cursor.execute("select accounts.name from accounts,gsessions where accounts.name = gsessions.name1")
            name_to = cursor.fetchall()[0][0]
            print name_to
            cursor.execute("select number from accounts where name = ?", (name_to,))
            to_number = cursor.fetchall()[0][0]
            message = client.messages.create(to=to_number, from_="+15183124106",
                                     body=msg)
            conn.commit()
        else:
            resp.message("It's not yet your turn!")
            
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
        ctfile = open('count.txt', "r+")
        count = int(ctfile.read())
        query = "update accounts set lfg = 0, ingame = 1, matchid = ? where number = ?"
        conn.execute(query, (count, from_number,))
        conn.execute(query, (count, num,))
        print count
        count += 1
        ctfile.seek(0)
        ctfile.write(str(count))
        ctfile.close()

    else:
        for x in range(5):
            foundgame = 0
            time.sleep(2)
            query = "select matchid from accounts where number = ? and ingame = 1"
            cursor.execute(query, (from_number,))
            row = cursor.fetchall()
            if len(row) != 0:
                message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Match found! Generating game id...")
                matchid = row[0][0]
                query = "select name from accounts where matchid = ?"
                cursor.execute(query, (matchid,))
                rows = cursor.fetchall()
                names = []
                for row in rows:
                    names.append(row)
                query = "insert into gsessions (matchid, turn, name1, name2, story) values (?,0,?,?,'')";
                conn.execute(query, (matchid,names[0][0],names[1][0],))
                firstname = names[0][0]
                query = "select number from accounts where name = ?"
                cursor.execute(query, (firstname,))
                to_number = cursor.fetchall()[0][0]
                message = client.messages.create(to=to_number, from_="+15183124106",
                                     body="You go first!")
                foundgame = 1
                break
        if not foundgame:
            message = client.messages.create(to=from_number, from_="+15183124106",
                                     body="Matchmaking failed! Try again next time.")
        query = "update accounts set lfg = 0 where number = ?"
        conn.execute(query, (from_number,))
    conn.commit()
    
if __name__ == "__main__":
    app.run(debug=True)