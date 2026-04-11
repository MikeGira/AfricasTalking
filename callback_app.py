import os
import sys
import ssl
import logging
import requests
import urllib3
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

# 1. NETWORK & SSL SUPPRESSION
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

# 2. LOGGING CONFIGURATION
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler = logging.FileHandler("at_gateway.log", encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 3. SERVICE INITIALIZATION
try:
    gemini_key = os.getenv("AT_GEMINI_API_Key") or os.getenv("AT_GEMINI_API_KEY")
    ai_client = genai.Client(api_key=gemini_key)
    
    AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
    AT_API_KEY = os.getenv("AT_API_KEY")
    AT_SMS_URL = "http://api.sandbox.africastalking.com/version1/messaging"

    logger.info("✅ OPSYNTH Services Initialized Successfully.")
except Exception as e:
    logger.error(f"❌ Initialization Failure: {e}")
    sys.exit(1)

app = Flask(__name__)

# 4. BUSINESS LOGIC LAYER

def relay_sms_direct(recipient, message):
    """Directly calls the AT API via HTTP to ensure delivery in sandbox."""
    payload = {
        "username": AT_USERNAME,
        "to": recipient,
        "message": message,
        "from": "9161" # Standard Sandbox Shortcode for simulator visibility
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apiKey": AT_API_KEY
    }
    try:
        response = requests.post(AT_SMS_URL, headers=headers, data=payload, verify=False)
        if response.status_code in [200, 201]:
            logger.info(f"📡 Gateway Success: {response.json()}")
        else:
            logger.error(f"❌ Gateway Error ({response.status_code}): {response.text}")
    except Exception as e:
        logger.error(f"❌ Network Exception: {e}")

def process_ai_intent(sender, text, retries=3):
    """Generates AI response with retry logic and multi-language support."""
    for attempt in range(retries):
        try:
            response = ai_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=text,
                config={
                    "system_instruction": (
                        "You are OPSYNTH, an AI for a logistics firm. "
                        "Keep replies professional, concise, and under 160 characters. "
                        "Always reply in the same language the user uses."
                    )
                }
            )
            ai_reply = response.text.replace('\n', ' ').strip()
            logger.info(f"🤖 AI Reply: {ai_reply}")

            relay_sms_direct(sender, ai_reply)
            return
                
        except Exception as e:
            if "503" in str(e) and attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"⚠️ Gemini busy (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Gemini Processing Error: {e}")
                break

# 5. WEBHOOK ROUTES

@app.route('/incoming/sms', methods=['POST'])
def handle_incoming_sms():
    data = request.form
    sender = data.get('from')
    text = data.get('text', '')

    logger.info(f"📩 From {sender}: {text}")
    process_ai_intent(sender, text)
    
    return jsonify({"status": "received"}), 200

@app.route('/callbacks/sms', methods=['POST'])
def handle_delivery_report():
    data = request.form
    msg_id = data.get('id')
    status = data.get('status')
    logger.info(f"📊 Delivery Report: {msg_id} -> {status}")
    return jsonify({"status": "accepted"}), 200

@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True, threaded=True)