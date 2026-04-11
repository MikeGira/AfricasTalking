import os
import requests
import urllib3
from dotenv import load_dotenv

# 1. NETWORK FIXES
# Suppress the insecure request warning since we are bypassing SSL for the sandbox
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# 2. CONFIGURATION
api_key = os.getenv("AT_API_KEY")
username = os.getenv("AT_USERNAME", "sandbox")

# Force HTTP to bypass SSL 'WRONG_VERSION_NUMBER' errors in local dev/ngrok
url = "http://api.sandbox.africastalking.com/version1/messaging"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "apiKey": api_key 
}

# The data payload
data = {
    "username": username,
    "to": "+250788285524", 
    "message": "Hello Mike, OPSYNTH is now online!",
    "from": "M-MONEY" 
}

# 3. EXECUTION
def send_test_sms():
    try:
        # Pass 'data' directly; requests encodes it as x-www-form-urlencoded
        # verify=False is used as a fallback, but the http:// URL is the primary fix
        response = requests.post(url, headers=headers, data=data, verify=False)
        
        print(f"--- AT Gateway Status: {response.status_code} ---")
        
        if response.status_code == 201 or response.status_code == 200:
            res_data = response.json()
            recipients = res_data.get('SMSMessageData', {}).get('Recipients', [])
            
            for r in recipients:
                print(f"✅ Sent to: {r['number']}")
                print(f"🆔 Message ID: {r['messageId']}")
                print(f"📊 Status: {r['status']}")
        else:
            print(f"❌ Failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    send_test_sms()