from twilio.rest import Client
from django.conf import settings
import re

def send_whatsapp_message(phone_number, message_body):
    """
    Sends a WhatsApp message via Twilio.
    Auto-formats phone numbers to E.164 (e.g., adds +91 if missing).
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # 1. CLEAN THE NUMBER
        # Remove spaces, dashes, parentheses
        clean_number = str(phone_number).strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # 2. FORMATTING LOGIC (For India +91)
        # If it starts with '0', remove it (e.g., 09866... -> 9866...)
        if clean_number.startswith('0'):
            clean_number = clean_number[1:]
        
        # If it doesn't start with '+', add '+91' (Default to India)
        if not clean_number.startswith('+'):
            clean_number = f"+91{clean_number}"
            
        # 3. CONSTRUCT TWILIO ADDRESS
        to_number = f"whatsapp:{clean_number}"
        from_number = settings.TWILIO_WHATSAPP_NUMBER

        # 4. SEND
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        
        print(f"✅ WhatsApp Sent to {clean_number}: {message.sid}")
        return message.sid

    except Exception as e:
        print(f"❌ WhatsApp Failed for {phone_number}: {str(e)}")
        return None