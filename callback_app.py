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

# 1. ENVIRONMENT & SSL CONFIGURATION
load_dotenv()
ENV = os.getenv("APP_ENV", "development")

if ENV == "development":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    os.environ['CURL_CA_BUNDLE'] = ''
    ssl._create_default_https_context = ssl._create_unverified_context

# 2. LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("at_gateway.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 3. SERVICE INITIALIZATION
try:
    # Use consistent key naming
    GEMINI_KEY = os.getenv("AT_GEMINI_API_KEY") or os.getenv("AT_GEMINI_API_Key")
    ai_client = genai.Client(api_key=GEMINI_KEY)
    
    # Africa's Talking Config
    AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
    AT_API_KEY = os.getenv("AT_API_KEY")
    AT_SMS_URL = "http://api.sandbox.africastalking.com/version1/messaging"
    SHORT_CODE = "9161"

    logger.info("✅ OPSYNTH Services Initialized Successfully.")
except Exception as e:
    logger.error(f"❌ Initialization Failure: {e}")
    sys.exit(1)

app = Flask(__name__)

# 4. BUSINESS LOGIC LAYER

def relay_sms_direct(recipient, message):
    """Handles outbound SMS delivery via Africa's Talking Gateway."""
    payload = {
        "username": AT_USERNAME,
        "to": recipient,
        "message": message,
        "from": SHORT_CODE
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apiKey": AT_API_KEY
    }
    try:
        # verify=False remains for local dev compatibility
        response = requests.post(AT_SMS_URL, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        logger.info(f"📡 SMS Gateway Success: {response.json()}")
    except Exception as e:
        logger.error(f"❌ SMS Gateway Exception: {e}")

def get_ai_response(content_input, is_voice=False):
    """Unified logic for generating Gemini responses."""
    system_prompt = (
        "You are OPSYNTH, a logistics and agricultural AI assistant. "
        "Keep responses professional and very concise. "
    )
    
    if is_voice:
        system_prompt += "This is a voice call. Use natural, spoken language. Reply in the user's language."
    else:
        system_prompt += "This is an SMS. Keep it under 160 characters. Use the user's language."

    try:
        response = ai_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=content_input,
            config={"system_instruction": system_prompt}
        )
        return response.text.replace('\n', ' ').strip()
    except Exception as e:
        logger.error(f"❌ Gemini AI Error: {e}")
        return "Nyamuneka mwongere mugerageze mukanya." # Kinyarwanda: Please try again later.

# 5. WEBHOOK ROUTES

@app.route('/incoming/sms', methods=['POST'])
def handle_sms():
    sender = request.form.get('from')
    text = request.form.get('text', '')
    logger.info(f"📩 Incoming SMS from {sender}: {text}")
    
    ai_reply = get_ai_response(text, is_voice=False)
    relay_sms_direct(sender, ai_reply)
    
    return jsonify({"status": "received"}), 200

@app.route('/incoming/voice', methods=['POST'])
def handle_voice_call():
    caller = request.form.get('callerNumber')
    logger.info(f"📞 Incoming call from: {caller}")
    
    # AT-XML greeting and instruction to record
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="man">Muraho! OPSYNTH iragufasha iki uyu munsi? Nyuma y'ijwi, vuga icyo wifuza hanyuma ukande urwego.</Say>
        <Record finishOnKey="#" maxLength="20" trimSilence="true" playBeep="true" callbackUrl="{request.host_url}voice/process"/>
    </Response>"""
    return xml_response, 200, {'Content-Type': 'application/xml'}

@app.route('/voice/process', methods=['POST'])
def handle_voice_audio():
    audio_url = request.form.get('recordingUrl')
    logger.info(f"🎙️ Processing Voice Data: {audio_url}")
    
    try:
        # Download the audio file
        audio_data = requests.get(audio_url, verify=False).content
        
        # Multimodal processing: Send bytes directly to Gemini
        ai_reply = get_ai_response(
            content_input=[{"mime_type": "audio/wav", "data": audio_data}, "Respond to this user's voice request."],
            is_voice=True
        )
        
        xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="man">{ai_reply}</Say>
            <Say voice="man">Murakoze guhamagara OPSYNTH.</Say>
        </Response>"""
    except Exception as e:
        logger.error(f"❌ Audio Processing Failure: {e}")
        xml_response = '<Response><Say>Error processing audio.</Say></Response>'

    return xml_response, 200, {'Content-Type': 'application/xml'}

@app.route('/callbacks/sms', methods=['POST'])
def sms_delivery_report():
    logger.info(f"📊 Report: {request.form.get('id')} -> {request.form.get('status')}")
    return jsonify({"status": "accepted"}), 200

@app.after_request
def add_ngrok_headers(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

if __name__ == '__main__':
    # Threaded=True is critical for handling the recording download while staying responsive
    app.run(port=5000, debug=True, threaded=True)