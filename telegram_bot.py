"""
Personal Telegram Weather Bot for North Macedonia & Balkans
Bilingual support: English & Russian
Zero external dependencies (uses Python standard library: urllib, json)

Features:
- Language selection upon entry (RU / EN)
- Web App button opening https://bmwgtrmpower-ops.github.io/gevgelija-weather/
- Send Location button for real-time elevation & micro-weather
- Storm & wire galloping push alerts
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEB_APP_URL = "https://bmwgtrmpower-ops.github.io/gevgelija-weather/"

USER_LANGS = {} # chat_id -> 'ru' | 'en'

def call_tg(method, data=None):
    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN is not set!")
        return None
    url = f"{API_URL}/{method}"
    headers = {"User-Agent": "WeatherBot/2.0"}
    req_data = None
    if data:
        headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[TG ERROR] {method}: {e}")
        return None

def get_weather_report(lat, lon, location_name, lang="ru"):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m"
        "&daily=precipitation_probability_max,precipitation_sum,wind_gusts_10m_max"
        "&forecast_days=2&timezone=auto&wind_speed_unit=ms"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'BalkanMeteoBot/2.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return f"Error / Ошибка: {e}"

    elevation = data.get('elevation', 0)
    cur = data.get('current', {})
    daily = data.get('daily', {})

    temp = round(cur.get('temperature_2m', 0))
    app = round(cur.get('apparent_temperature', temp))
    hum = cur.get('relative_humidity_2m', 0)
    wind = round(cur.get('wind_speed_10m', 0), 1)
    gusts = round(daily.get('wind_gusts_10m_max', [0])[0], 1)
    rain_prob = daily.get('precipitation_probability_max', [0])[0]
    wcode = cur.get('weather_code', 0)

    if lang == "en":
        cond = "Clear"
        if wcode in [1, 2]: cond = "Partly Cloudy"
        elif wcode == 3: cond = "Overcast"
        elif wcode in [45, 48]: cond = "Fog"
        elif wcode in [51, 53, 55, 61, 63, 65, 80]: cond = "Rain"
        elif wcode >= 95: cond = "Thunderstorm"

        wire_alert = ""
        if gusts >= 17:
            wire_alert = f"\n\n🚨 <b>STORM ALERT:</b> Wind gusts up to <b>{gusts} m/s</b>! High danger of wire slapping on poles. Unplug heaters tonight!"
        elif gusts >= 13:
            wire_alert = f"\n\n⚠️ <b>STRONG WIND:</b> Gusts up to <b>{gusts} m/s</b> outside."

        return (
            f"📍 <b>{location_name}</b> ({elevation:.0f} m)\n\n"
            f"🌡 <b>Temperature:</b> {temp:+}°C (feels like {app:+}°C)\n"
            f"☁️ <b>Conditions:</b> {cond}\n"
            f"🌧 <b>Rain chance today:</b> {rain_prob}%\n"
            f"💨 <b>Wind:</b> {wind} m/s (gusts {gusts} m/s)\n"
            f"💧 <b>Humidity:</b> {hum}%"
            f"{wire_alert}"
        )
    else:
        cond = "Ясно"
        if wcode in [1, 2]: cond = "Переменная облачность"
        elif wcode == 3: cond = "Пасмурно"
        elif wcode in [45, 48]: cond = "Туман"
        elif wcode in [51, 53, 55, 61, 63, 65, 80]: cond = "Идёт дождь"
        elif wcode >= 95: cond = "Гроза"

        wire_alert = ""
        if gusts >= 17:
            wire_alert = f"\n\n🚨 <b>ШТОРМ:</b> Порывы ветра до <b>{gusts} м/с</b>! Риск схлёстывания фазных проводов на столбах. Выключите обогреватели из розеток на ночь!"
        elif gusts >= 13:
            wire_alert = f"\n\n⚠️ <b>СИЛЬНЫЙ ВЕТЕР:</b> Порывы до <b>{gusts} м/с</b>, на улице раскачивает провода."

        return (
            f"📍 <b>{location_name}</b> ({elevation:.0f} м)\n\n"
            f"🌡 <b>Температура:</b> {temp:+}°C (ощущается как {app:+}°C)\n"
            f"☁️ <b>Погода:</b> {cond}\n"
            f"🌧 <b>Шанс дождя сегодня:</b> {rain_prob}%\n"
            f"💨 <b>Ветер:</b> {wind} м/с (порывы до {gusts} м/с)\n"
            f"💧 <b>Влажность:</b> {hum}%"
            f"{wire_alert}"
        )

def send_welcome(chat_id, lang="ru"):
    if lang == "en":
        text = (
            "👋 <b>Welcome to Balkan Meteo Hub!</b>\n\n"
            "• Tap <b>Open App</b> to launch the full interactive weather station.\n"
            "• Tap <b>Send Location</b> to get micro-climate data anywhere you walk.\n"
            "• Switch language anytime with the button below."
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Open App", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Send Location (GPS)", "request_location": True}],
                [{"text": "🇷🇺 Русский язык"}]
            ],
            "resize_keyboard": True
        }
    else:
        text = (
            "👋 <b>Добро пожаловать в Балканскую Метеостанцию!</b>\n\n"
            "• Нажмите <b>Открыть приложение</b>, чтобы открыть интерактивную метеостанцию.\n"
            "• Нажмите <b>Отправить геопозицию</b> для прогноза в любой точке на прогулке.\n"
            "• Поменять язык можно кнопкой ниже."
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Открыть приложение", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Отправить геопозицию (GPS)", "request_location": True}],
                [{"text": "🇬🇧 English"}]
            ],
            "resize_keyboard": True
        }

    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    })

def handle_message(msg):
    chat_id = msg.get("chat", {}).get("id")
    if not chat_id:
        return

    lang = USER_LANGS.get(chat_id, "ru")

    if "location" in msg:
        loc = msg["location"]
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        rep = get_weather_report(lat, lon, "GPS Location" if lang=="en" else "Точка на карте", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

    text = msg.get("text", "").strip()

    if text in ["/start", "/help"]:
        send_welcome(chat_id, lang)
        return

    if text in ["🇬🇧 English", "/en"]:
        USER_LANGS[chat_id] = "en"
        send_welcome(chat_id, "en")
        return

    if text in ["🇷🇺 Русский язык", "🇷🇺 Русский", "/ru"]:
        USER_LANGS[chat_id] = "ru"
        send_welcome(chat_id, "ru")
        return

if __name__ == "__main__":
    print("Bilingual Telegram Weather Bot Engine Ready.")
