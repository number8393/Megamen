import time
import requests
import yfinance as yf
import pytz
from datetime import datetime

TG_TOKEN = "8094752756:AAFUdZn4XFlHiZOtV-TXzMOhYFlXKCFVoEs"
TG_CHAT_ID = "5556108366"

PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X",
    "NZDUSD=X", "USDCAD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X"
]

astana_tz = pytz.timezone("Asia/Almaty")

def is_trading_time():
    now = datetime.now(astana_tz)
    return 6 <= now.hour < 22

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Ошибка Telegram:", e)

def analyze_pair(pair):
    data = yf.download(pair, period="2d", interval="15m", progress=False)
    if data.empty or len(data) < 4:
        return None

    volume_now = data["Volume"].iloc[-1]
    volume_avg = data["Volume"].rolling(5).mean().iloc[-1]
    volume_signal = "🔥 Высокий объём" if volume_now > volume_avg * 1.2 else "📉 Средний объём"

    last = data.iloc[-1]
    prev = data.iloc[-2]
    candle_signal = "🚀 Бычий" if last["Close"] > last["Open"] and prev["Close"] < prev["Open"] else \
                    "🐻 Медвежий" if last["Close"] < last["Open"] and prev["Close"] > prev["Open"] else "❌ Нет сигнала"

    change = abs(data["Close"].pct_change().iloc[-1])
    confidence = round(change * 100, 2)
    price = round(last["Close"], 5)
    duration = 5 if confidence < 0.5 else 15

    if candle_signal == "❌ Нет сигнала" or confidence < 0.15:
        return None

    return {
        "pair": pair.replace("=X", ""),
        "price": price,
        "volume": volume_signal,
        "candle": candle_signal,
        "confidence": confidence,
        "duration": duration
    }

def main():
    send_telegram("🤖 Бот запущен и анализирует рынок...")

    while True:
        if is_trading_time():
            for pair in PAIRS:
                result = analyze_pair(pair)
                if result:
                    msg = (
                        f"📡 <b>Сигнал</b> на <b>{result['pair']}</b>\n"
                        f"💰 Цена: {result['price']}\n"
                        f"🕯 Свечи: {result['candle']}\n"
                        f"📊 Объём: {result['volume']}\n"
                        f"📈 Уверенность: {result['confidence']}%\n"
                        f"⏱ Сделка на: {result['duration']} мин\n"
                        f"🧠 Стратегия: Smoke FX / Smart Money"
                    )
                    send_telegram(msg)
                else:
                    print(f"{pair} — сигналов нет")
        else:
            print("⏳ Вне торгового времени (Астана)")
        time.sleep(60)

if __name__ == "__main__":
    main()
