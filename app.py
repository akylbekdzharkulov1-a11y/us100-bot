import os, time, threading, requests
from flask import Flask
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "@xauusdakyl"
app = Flask(__name__)

def send_telegram(text):
    try:
        if not TELEGRAM_TOKEN:
            print("NO TOKEN")
            return
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
        print(f"TG {r.status_code}")
    except Exception as e:
        print(f"TG err {e}")

def get_history():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENDX?interval=5m&range=5d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        j = r.json()['chart']['result'][0]
        closes = j['indicators']['quote'][0]['close']
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
    gains = 0
    losses = 0
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

    # ATR туура эсеп
    atr = 0
    for i in range(-14, 0):
        atr += abs(closes[i] - closes[i-1])
    atr = atr / 14

    uptrend = price > ema50 and ema50 > ema200
    downtrend = price < ema50 and ema50 < ema200
    last_high = max(closes[-20:-1])
    last_low = min(closes[-20:-1])

    score = 0
    reasons = []
    if uptrend:
        score += 30
        reasons.append("EMA 50>200 UPTREND")
    if downtrend:
        score += 30
        reasons.append("EMA 50<200 DOWNTREND")
    if uptrend and 45 < rsi < 65:
        score += 20
        reasons.append(f"RSI {rsi:.1f} Pullback")
    if downtrend and 35 < rsi < 55:
        score += 20
        reasons.append(f"RSI {rsi:.1f} Pullback")
    if price > last_high * 1.0005:
        score += 20
        reasons.append("Breakout HIGH")
    if price < last_low * 0.9995:
        score += 20
        reasons.append("Breakdown LOW")

    if score >= 60:
        direction = "BUY" if uptrend else "SELL"
        if direction == "BUY":
            tp1 = price + atr*1.5
            tp2 = price + atr*3
            sl = price - atr*1.2
        else:
            tp1 = price - atr*1.5
            tp2 = price - atr*3
            sl = price + atr*1.2

        msg = f"*US100 {score}% SETUP - {direction}*\n\nPrice: {price:.2f}\nRSI: {rsi:.1f}\n\nReasons:\n" + "\n".join(reasons) + f"\n\nENTRY: {price:.2f}\nSL: {sl:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\n\n@xauusdakyl {datetime.now().strftime('%H:%M')}"
        return msg, score
    return None

def bot_loop():
    print("Bot started 60-100%")
    send_telegram("US100 Bot 60-100% логика менен кайра жанды! @xauusdakyl")
    last = 0
    while True:
        try:
            res = analyze()
            if res and time.time() - last > 3600:
                send_telegram(res[0])
                last = time.time()
            else:
                print("No setup")
        except Exception as e:
            print(f"Loop
