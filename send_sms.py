from twilio.rest import TwilioRestClient

# Find these values at https://twilio.com/user/account
account_sid = "ACb31814cf701c394d4bea1fb2b87c8b2c"
auth_token = "38b85885594ba31c9d06148f2fc6afce"
client = TwilioRestClient(account_sid, auth_token)
 
message = client.messages.create(to="+15184951131", from_="+15183124106",
                                     body="i like turtles")