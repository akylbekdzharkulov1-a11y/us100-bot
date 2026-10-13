import os
from flask import Flask
import yfinance as yf
import requests
import time
import threading
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = "@xauusdakyl"
TICKER = "^NDX"

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except: pass

def check_us100():
    while True:
        try:
            data = yf.download(TICKER, period="2d", interval="15m")
            close = data['Close']
            ema9 = close.ewm(span=9).mean().iloc[-1]
            ema21 = close.ewm(span=21).mean().iloc[-1]
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            price = close.iloc[-1]
            signal = ""
            if ema9 > ema21 and float(rsi) < 70 and float(rsi) > 50:
                signal = f"🟢 US100 BUY {float(price):.2f} RSI:{float(rsi):.1f}"
            elif ema9 < ema21 and float(rsi) > 30 and float(rsi) < 50:
                signal = f"🔴 US100 SELL {float(price):.2f} RSI:{float(rsi):.1f}"
            if signal:
                send_telegram(signal)
        except Exception as e:
            print(e)
        time.sleep(900)

@app.route('/')
def home():
    return f"US100 Bot Live -> @xauusdakyl {datetime.now()}"

threading.Thread(target=check_us100, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
