"""
Personal Telegram Weather Bot for North Macedonia & Balkans
Zero external dependencies (uses standard python library: urllib, json)

Features:
- Send Location button: Send any GPS pin (village, mountain trail, park) -> instant elevation-aware forecast.
- City / Village search: Type any name ("Скопье", "Маврово", "Охрид", "Гевгелия").
- Rain radar / 3-hour precipitation probability.
- Clothing & comfort advice.
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys

# Replace with your Telegram Bot Token from @BotFather
# Or pass via environment variable TELEGRAM_BOT_TOKEN
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def call_tg(method, data=None):
    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN is not set!")
        return None
    url = f"{API_URL}/{method}"
    headers = {"User-Agent": "WeatherBot/1.0"}
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

def get_weather_for_coords(lat, lon, location_name="Текущее местоположение"):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,is_day,precipitation,weather_code,wind_speed_10m,surface_pressure"
        "&hourly=temperature_2m,precipitation_probability,precipitation"
        "&forecast_days=2&timezone=auto"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'PersonalMeteoBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return f"Не удалось получить погоду: {e}"

    elevation = data.get('elevation', 0)
    curr = data.get('current', {})
    hourly = data.get('hourly', {})

    temp = round(curr.get('temperature_2m', 0))
    app_temp = round(curr.get('apparent_temperature', temp))
    humidity = curr.get('relative_humidity_2m', 0)
    wind_spd = round(curr.get('wind_speed_10m', 0))
    precip = curr.get('precipitation', 0.0)
    wcode = curr.get('weather_code', 0)

    # Precipitation risk in next 3 hours
    times = hourly.get('time', [])
    probs = hourly.get('precipitation_probability', [])
    curr_time_str = curr.get('time', '')
    
    rain_risk_soon = False
    max_prob = 0
    if curr_time_str in times:
        idx = times.index(curr_time_str)
        next_probs = probs[idx:idx+4]
        if next_probs:
            max_prob = max(next_probs)
            if max_prob >= 40:
                rain_risk_soon = True

    cond_desc = "ясно и солнечно"
    if wcode in [1, 2, 3]:
        cond_desc = "переменная облачность" if wcode <= 2 else "пасмурно"
    elif wcode in [45, 48]:
        cond_desc = "туман"
    elif wcode in [51, 53, 55, 61, 63, 65, 80, 81]:
        cond_desc = "идёт дождь"
    elif wcode in [71, 73, 75, 77, 85, 86]:
        cond_desc = "идёт снег"
    elif wcode >= 95:
        cond_desc = "гроза"

    if temp >= 22:
        clothes = "Футболка или лёгкая рубашка."
    elif temp >= 16:
        clothes = "Лёгкая кофта, худи или тонкая ветровка."
    elif temp >= 11:
        clothes = "Плотное худи с жилеткой или осенняя куртка."
    elif temp >= 5:
        clothes = "Тёплая куртка, желательно не продуваемая."
    else:
        clothes = "Зимняя тёплая куртка, шапка."

    msg = (
        f"📍 <b>{location_name}</b> (высота {elevation:.0f} м)\n\n"
        f"🌡 <b>Температура:</b> {temp:+}°C (ощущается как {app_temp:+}°C)\n"
        f"☁️ <b>Состояние:</b> {cond_desc}\n"
        f"💧 <b>Влажность:</b> {humidity}%\n"
        f"💨 <b>Ветер:</b> {wind_spd} км/ч\n\n"
    )

    if precip > 0:
        msg += f"☔️ <b>Осадки:</b> Сейчас капает ({precip} мм). Обязательно возьмите зонт!\n"
    elif rain_risk_soon:
        msg += f"⚠️ <b>Внимание:</b> В ближайшие часы вероятность дождя {max_prob}%. Зонт лучше прихватить.\n"
    else:
        msg += f"☀️ <b>Дождя нет</b>, в ближайшие часы сухо (риск осадков {max_prob}%).\n"

    msg += f"👕 <b>Что надеть:</b> {clothes}"
    return msg

def geocode_city(city_query):
    # Geocoding via Open-Meteo Geocoding API
    encoded = urllib.parse.quote(city_query)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=ru&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'PersonalMeteoBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('results', [])
            if results:
                r = results[0]
                name = r.get('name')
                country = r.get('country', '')
                admin1 = r.get('admin1', '')
                full_name = f"{name}, {admin1} ({country})".replace(",  ", ", ")
                return r['latitude'], r['longitude'], full_name
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None, None

def send_welcome(chat_id):
    keyboard = {
        "keyboard": [
            [{"text": "📍 Где я сейчас? (Отправить геопозицию)", "request_location": True}],
            [{"text": "🏠 Гевгелия (Дом)"}, {"text": "🏙 Скопье (Родители)"}],
            [{"text": "🏔 Маврово (Горы)"}, {"text": "🌊 Охрид (Озеро)"}]
        ],
        "resize_keyboard": True
    }
    text = (
        "👋 <b>Привет! Я твоя персональная балканская метеостанция.</b>\n\n"
        "Я умею:\n"
        "• Принимать геопозицию с телефона (в любой деревне или на прогулке) и давать мгновенную сводку погоды с учётом высоты.\n"
        "• Показывать погоду в любом городе или селе — просто напиши название (например, <i>Скопье</i> или <i>Берово</i>).\n"
        "• Советовать, что надеть (худи, куртку, футболку) и предупреждать о дожде в ближайшие 3 часа.\n\n"
        "Нажми кнопку ниже или напиши название места:"
    )
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

    # 1. Location message
    if "location" in msg:
        loc = msg["location"]
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        report = get_weather_for_coords(lat, lon, "Точка на карте")
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
        return

    text = msg.get("text", "").strip()

    if text in ["/start", "/help"]:
        send_welcome(chat_id)
        return

    if text == "🏠 Гевгелия (Дом)":
        report = get_weather_for_coords(41.1465, 22.5042, "Бульвар Гевгелия 18")
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
        return

    if text == "🏙 Скопье (Родители)":
        report = get_weather_for_coords(41.9981, 21.4254, "Скопье (Центр)")
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
        return

    if text == "🏔 Маврово (Горы)":
        report = get_weather_for_coords(41.7011, 20.7389, "Маврово (Горнолыжный курорт 1300м)")
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
        return

    if text == "🌊 Охрид (Озеро)":
        report = get_weather_for_coords(41.1128, 20.8019, "Охрид (Набережная)")
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
        return

    # Text search
    lat, lon, place_name = geocode_city(text)
    if lat is not None:
        report = get_weather_for_coords(lat, lon, place_name)
        call_tg("sendMessage", {"chat_id": chat_id, "text": report, "parse_mode": "HTML"})
    else:
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": f"Не удалось найти место «{text}». Попробуйте отправить геопозицию кнопкой или уточнить название.",
            "parse_mode": "HTML"
        })

def run_polling():
    print("Starting Telegram Bot long-polling...")
    offset = 0
    while True:
        try:
            res = call_tg("getUpdates", {"offset": offset, "timeout": 30})
            if res and res.get("ok"):
                for upd in res.get("result", []):
                    offset = upd["update_id"] + 1
                    if "message" in upd:
                        handle_message(upd["message"])
            time.sleep(0.5)
        except Exception as e:
            print(f"Polling loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Please set TELEGRAM_BOT_TOKEN environment variable or put it into BOT_TOKEN.")
    else:
        run_polling()
