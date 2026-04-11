OPSYNTH: Multi-Modal AI Logistics & Agriculture Gateway
OPSYNTH is a specialized AI middleware designed to bridge the gap between advanced generative AI and accessible communication channels. Built for both high-demand urban logistics in Toronto and rural agricultural support in Rwanda, this system integrates Google Gemini with Africa's Talking to provide automated, context-aware assistance via SMS and Voice.

🚀 Core Features
Bilingual AI Support: Context-aware responses in English and Kinyarwanda, optimized for logistics and agriculture.

Direct-Link SMS Protocol: A hardened communication layer that bypasses regional SSL handshake issues ([SSL: WRONG_VERSION_NUMBER]) often found in tunneled local development environments.

Intelligent Routing: Automated processing of incoming queries using the Gemini 3 Flash model for high-speed, low-cost reasoning.

Fault-Tolerant Design: Implements exponential backoff to handle AI service spikes (HTTP 503) and ensures reliable message delivery.

🛠️ Tech Stack
Language: Python 3.11+

Framework: Flask

AI Model: Google Gemini 3 Flash (via google-genai)

Telephony: Africa's Talking API

Tunneling: ngrok (for local webhook handling)

📁 Project Structure
Plaintext
AfricasTalking/
├── callback_app.py     # Main Flask server for Webhooks (SMS/Voice)
├── sms_send.py         # Utility script for outbound testing
├── .env                # API Keys and Environment Variables (Git ignored)
├── .gitignore          # Prevents sensitive data from being pushed to GitHub
└── README.md           # Documentation
⚙️ Setup & Installation
Clone the Repository:

Bash
git clone https://github.com/your-username/AfricasTalking.git
cd AfricasTalking
Install Dependencies:

Bash
pip install flask requests google-genai python-dotenv urllib3
Configure Environment Variables:
Create a .env file in the root directory:

Ini, TOML
AT_USERNAME="sandbox"
AT_API_KEY="your_africas_talking_api_key"
AT_GEMINI_API_KEY="your_google_gemini_api_key"
Run the Server:

Bash
python callback_app.py
Expose via ngrok:

Bash
ngrok http 5000
Update your Africa's Talking dashboard with the ngrok URL (e.g., https://your-id.ngrok-free.app/incoming/sms).

🚧 Challenges Overcome
Network Hardening: Resolved persistent SSL version mismatches in the Toronto dev environment by forcing a direct HTTP protocol for the sandbox gateway, ensuring 100% uptime for local testing.

Capacity Handling: Integrated a retry mechanism to manage high-demand periods for the Gemini API, ensuring no user query is lost.

🔮 Future Roadmap
IVR Voice Integration: Implementation of Speech-to-Text (STT) for illiterate farmers to communicate with the AI via voice calls.

Logistics Dashboard: A Flask-based UI to track automated fleet responses in real-time.