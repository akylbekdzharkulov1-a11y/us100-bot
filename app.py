import os, time, threading, requests
from flask import Flask
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "@xauusdakyl"
app = Flask(__name__)

def send_telegram(text):
    try:
        if not TELEGRAM_TOKEN: return
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        print(e)

def get_history():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENDX?interval=5m&range=5d"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        j = r.json()['chart']['result'][0]
        closes = j['indicators']['quote'][0]['close']
        closes = [c for c in closes if c is not None]
        return closes
    except:
        return None

def calc_ema(data, period):
    if len(data) < period: return None
    k = 2/(period+1)
    ema = sum(data[:period])/period
    for p in data[period:]:
        ema = p*k + ema*(1-k)
    return ema

def calc_rsi(data, period=14):
    if len(data) < period+1: return 50
    g=l=0
    for i in range(1, period+1):
        d = data[-i] - data[-i-1]
        if d>0: g+=d
        else: l-=d
    if l==0: return 100
    return 100 - (100/(1+g/l))

def analyze():
    closes = get_history()
    if not closes or len(closes) < 200: return None
    price = closes[-1]
    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)
    rsi = calc_rsi(closes)
    atr = sum(abs(closes[i]-closes[i-1]) for i in range(-14,0)) / 14
    up = price>ema50 and ema50>ema200
    down = price<ema50 and ema50<ema200
    last_high = max(closes[-20:-1])
    last_low = min(closes[-20:-1])
    score=0
    reasons=[]
    if up:
        score+=30; reasons.append("UPTREND EMA50>200")
    if down:
        score+=30; reasons.append("DOWNTREND EMA50<200")
    if up and 45<rsi<65:
        score+=20; reasons.append(f"RSI {rsi:.1f} Pullback")
    if down and 35<rsi<55:
        score+=20; reasons.append(f"RSI {rsi:.1f} Pullback")
    if price>last_high*1.0005:
        score+=20; reasons.append("Breakout HIGH")
    if price<last_low*0.9995:
        score+=20; reasons.append("Breakdown LOW")
    if score>=60:
        d="BUY" if up else "SELL"
        if d=="BUY":
            tp1=price+atr*1.5; tp2=price+atr*3; sl=price-atr*1.2
        else:
            tp1=price-atr*1.5; tp2=price-atr*3; sl=price+atr*1.2
        msg=f"*US100 {score}% SETUP - {d}*\n\nPrice: {price:.2f}\nRSI: {rsi:.1f}\n\nReasons:\n" + "\n".join(reasons) + f"\n\nENTRY: {price:.2f}\nSL: {sl:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\n\n@xauusdakyl"
        return msg, score
    return None

def bot_loop():
    print("Bot started")
    send_telegram("✅ US100 60-100% Bot Live @xauusdakyl")
    last=0
    while True:
        try:
            res=analyze()
            if res and time.time()-last>3600:
                send_telegram(res[0]); last=time.time()
        except Exception as e:
            print(e)
        time.sleep(300)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    c=get_history(); p=c[-1] if c else 0
    return f"US100 Live {p}"

@app.route('/test')
def test():
    r=analyze()
    if r:
        send_telegram(r[0]); return f"Sent {r[1]}%"
    else:
        c=get_history(); p=c[-1] if c else 0
        send_telegram(f"TEST US100: {p:.2f} - 60%+ setup yok, bot ishtep jatat @xauusdakyl")
        return "Test sent"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
