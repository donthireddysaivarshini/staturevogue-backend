# test_twilio.py
import os
from twilio.rest import Client

# 1. PASTE YOUR KEYS DIRECTLY HERE (Do not use settings.py for this test)
SID = "ACe69ca844f30d114d76ab6d339b3205d1"  # Paste your Account SID here
TOKEN = "62ffb10fe08fa7c38b45b6254e60e8e7"  # Paste your Auth Token here

def test_connection():
    print(f"Testing with SID: {SID[:6]}... (Hidden)")
    print(f"Testing with Token Length: {len(TOKEN)}")

    try:
        client = Client(SID, TOKEN)
        # Attempt to fetch account details (Cheapest way to test Auth)
        account = client.api.accounts(SID).fetch()
        print("\n✅ SUCCESS! Credentials are valid.")
        print(f"Account Name: {account.friendly_name}")
        print(f"Status: {account.status}")
    except Exception as e:
        print("\n❌ FAILED! Twilio rejected these keys.")
        print(f"Error Message: {e}")

if __name__ == "__main__":
    test_connection()