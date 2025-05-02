# coreEat/payments/mobile/twilio_utils.py
import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

def normalize_phone_number(phone):
    """Convert local Zambian phone number to E.164 format."""
    phone = phone.strip()
    if phone.startswith('0'):
        return '+260' + phone[1:]
    elif not phone.startswith('+'):
        return '+260' + phone
    return phone

def send_sms(to_phone, message_body):
    """
    Send an SMS using Twilio with settings from Django configuration.
    
    Args:
        to_phone (str): The recipient's phone number (e.g., '0971234567' or '+260971234567').
        message_body (str): The text content of the SMS.
    
    Returns:
        dict: {'success': bool, 'message': str, 'sid': str (if successful)}
    """
    if not settings.TWILIO_ENABLED:
        logger.info("Twilio SMS is disabled in settings.")
        return {'success': False, 'message': 'SMS sending is disabled'}

    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
        logger.warning("Twilio credentials are not set in settings. SMS will not be sent.")
        return {'success': False, 'message': 'Twilio credentials missing'}

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        normalized_phone = normalize_phone_number(to_phone)
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=normalized_phone
        )
        logger.info(f"SMS sent to {normalized_phone}: {message.sid}")
        return {'success': True, 'message': 'SMS sent successfully', 'sid': message.sid}
    except TwilioRestException as e:
        logger.error(f"Twilio SMS failed: {str(e)}")
        return {'success': False, 'message': f"SMS failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error sending SMS: {str(e)}")
        return {'success': False, 'message': f"Unexpected error: {str(e)}"}
    
    
    # Download the helper library from https://www.twilio.com/docs/python/install
