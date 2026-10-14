import os, time, threading, requests, math
from flask import Flask
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "@xauusdakyl"
app = Flask(__name__)

def send_telegram(text):
    try:
        if not TELEGRAM_TOKEN: return
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=15)
        print(f"TG {r.status_code}")
    except Exception as e:
        print(f"TG err {e}")

def get_history():
    """Yahoo Chart API - 429 болбойт"""
    try:
        # 5m candles, 5 days
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENDX?interval=5m&range=5d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        j = r.json()['chart']['result'][0]
        closes = j['indicators']['quote'][0]['close']
        # тазалоо
        closes = [c for c in closes if c is not None]
        return closes
    except Exception as e:
        print(f"History err {e}")
        return None

def calc_ema(data, period):
    if len(data) < period: return None
    k = 2/(period+1)
    ema = sum(data[:period])/period
    for price in data[period:]:
        ema = price*k + ema*(1-k)
    return ema

def calc_rsi(data, period=14):
    if len(data) < period+1: return 50
    gains=losses=0
    for i in range(1, period+1):
        diff = data[-i] - data[-i-1]
        if diff>0: gains+=diff
        else: losses-=diff
    if losses==0: return 100
    rs = gains/losses
    return 100 - (100/(1+rs))

def analyze():
    closes = get_history()
    if not closes or len(closes) < 200:
        return None

    price = closes[-1]
    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)
    rsi = calc_rsi(closes, 14)

    # ATR үчүн
    atr = sum(abs(closes[i]-closes[i-1]) for i
