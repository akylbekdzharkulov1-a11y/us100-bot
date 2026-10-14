import os, time, threading, requests
from flask import Flask

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "@xauusdakyl"

app = Flask(__name__)

def send_telegram(text):
    if not TELEGRAM_TOKEN:
        print("NO TOKEN!")
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram send: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"Telegram error: {e}")

def get_price():
    # Прямой запрос без yfinance - обходит 429
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENDX?interval=5m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except Exception as e:
        print(f"Price error: {e}")
        return None

def bot_loop():
    print("Bot loop started")
    send_telegram("✅ US100 Bot иштеп баштады! @xauusdakyl")
    while True:
        price = get_price()
        print(f"Price check: {price}")
        if price:
            # Простой сигнал для теста - каждую проверку шлем
            # Потом заменишь на свою логику
            if int(time.time()) % 900 < 60: # каждые 15 мин
                msg = f"📊 *US100 (NAS100)*\n💰 Баа: `{price:.2f}`\n\n⚠️ Тест сигнал - бот иштеп жатат!\n\n@xauusdakyl"
                send_telegram(msg)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return f"US100 Bot Live -> {CHAT_ID} {time.ctime()} Price: {get_price()}"

@app.route('/test')
def test():
    send_telegram("🚀 TEST: US100 bot @xauusdakyl каналына туташты! Баа: " + str(get_price()))
    return "Test sent to channel!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
