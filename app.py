# === Flask Backend for Price Alert System ===

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import threading
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
from flask import send_from_directory


app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

# --- In-memory alert list (use DB in production) ---
alerts = []

# --- Email Settings (replace with your credentials) ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'krishjshah1@gmail.con'
EMAIL_PASSWORD = 'kbsc atdy qmfw dmnm'

# --- Helper: Send Email ---
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        print(f"✅ Email sent to {to_email}")

# --- Helper: Scrape Price (simple HTML based method) ---
def get_price(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Customize this selector based on website structure
        price_element = soup.select_one('.leftPrice.pull-right')
        if not price_element:
            return None
        price_text = price_element.get_text(strip=True).replace("₹", "").replace(",", "")
        return int(price_text)
    except:
        return None

# --- Background Job to Monitor Prices ---
def price_monitor_loop():
    while True:
        print("🔄 Running price monitor loop...")
        for alert in alerts:
            price = get_price(alert['url'])
            print(f"Checking: {alert['url']}")
            print(f"Found price: {price}, Target price: {alert['target']}")
            if price is not None and price <= alert['target'] and not alert['notified']:
                print(f"✅ Sending email to {alert['email']}")
                send_email(
                    alert['email'],
                    "📉 Price Drop Alert!",
                    f"Price dropped to ₹{price}!\n{alert['url']}"
                )
                alert['notified'] = True
        time.sleep(30)  # check every 30 seconds temporarily


# --- API Route to Create Alert ---
@app.route('/create-alert', methods=['POST'])
def create_alert():
    data = request.get_json()
    alerts.append({
        'url': data['url'],
        'target': int(data['price']),
        'email': data['email'],
        'notified': False
    })
    return jsonify({'status': 'alert created'})

if __name__ == '__main__':
    threading.Thread(target=price_monitor_loop, daemon=True).start()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)


