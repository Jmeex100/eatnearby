from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Hardcode credentials for testing
account_sid = 'AC82fd9f51a19dc28febd379fe64fe4e57'
auth_token = '2bd58a7286c569902174c81c79c16fbe'
twilio_number = '+19897873604'

client = Client(account_sid, auth_token)

try:
    message = client.messages.create(
        body="Test SMS from Twilio",
        from_=twilio_number,
        to="+260973546375"
    )
    print(f"SMS sent successfully! SID: {message.sid}")
except TwilioRestException as e:
    print(f"Twilio error: {str(e)}")