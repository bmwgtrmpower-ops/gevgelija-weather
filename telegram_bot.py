"""
Bilingual Telegram Weather Bot Engine for @macedonia_meteo_bot
- Onboarding on /start: instant inline buttons "English or Russian?"
- Inline edit callback confirmation + Full Main Menu
- Settings button (⚙️ Settings / ⚙️ Настройки) to switch language anytime
- Full Web App integration (Telegram Mini App)
- Grid Storm Sentinel (wind gusts & wire galloping protection for heaters)
- GPS location handler with barometric pressure, rain probability and elevation
- Zero external dependencies (urllib, json)
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEB_APP_URL = "https://bmwgtrmpower-ops.github.io/gevgelija-weather/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANG_FILE = os.path.join(BASE_DIR, "user_languages.json")
USER_LANGS = {}

def load_user_languages():
    global USER_LANGS
    if os.path.exists(LANG_FILE):
        try:
            with open(LANG_FILE, "r", encoding="utf-8") as f:
                USER_LANGS = json.load(f)
        except Exception:
            USER_LANGS = {}

def save_user_language(chat_id, lang):
    USER_LANGS[str(chat_id)] = lang
    try:
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_LANGS, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving lang: {e}")

load_user_languages()

def call_tg(method, data=None):
    if not BOT_TOKEN:
        print("[ERROR] BOT_TOKEN is not set!")
        return None
    url = f"{API_URL}/{method}"
    headers = {"User-Agent": "MacedoniaMeteoBot/2.0"}
    req_data = None
    if data:
        headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[TG ERROR] {method}: {e}")
        return None

def get_weather_report(lat, lon, location_name, lang="ru"):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,surface_pressure"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_gusts_10m_max"
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
    rain_sum = daily.get('precipitation_sum', [0.0])[0]
    wcode = cur.get('weather_code', 0)
    press_mm = round(cur.get('surface_pressure', 1013) * 0.750062)

    if lang == "en":
        cond = "Clear"
        if wcode in [1, 2]: cond = "Partly Cloudy"
        elif wcode == 3: cond = "Overcast"
        elif wcode in [45, 48]: cond = "Fog"
        elif wcode in [51, 53, 55, 61, 63, 65, 80]: cond = "Rain"
        elif wcode >= 95: cond = "Thunderstorm"

        wire_alert = ""
        if gusts >= 17:
            wire_alert = f"\n\n🚨 <b>STORM ALERT:</b> Wind gusts up to <b>{gusts} m/s</b>! High danger of wire galloping & 380V phase surges. <b>Unplug space heaters and electronics tonight!</b>"
        elif gusts >= 13:
            wire_alert = f"\n\n⚠️ <b>STRONG WIND:</b> Gusts up to <b>{gusts} m/s</b> outside. Overhead wires will sway."
        else:
            wire_alert = f"\n\n⚡️ <b>Power Grid:</b> Safe. Gusts {gusts} m/s. Overhead lines stable."

        return (
            f"📍 <b>{location_name}</b> (elevation {elevation:.0f} m)\n\n"
            f"🌡 <b>Temperature:</b> {temp:+}°C (feels like {app:+}°C)\n"
            f"☁️ <b>Conditions:</b> {cond}\n"
            f"🌧 <b>Rain chance today:</b> {rain_prob}% ({rain_sum} mm)\n"
            f"💨 <b>Wind:</b> {wind} m/s (gusts up to {gusts} m/s)\n"
            f"💧 <b>Humidity:</b> {hum}% • <b>Pressure:</b> {press_mm} mmHg"
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
            wire_alert = f"\n\n🚨 <b>ШТОРМОВОЕ ПРЕДУПРЕЖДЕНИЕ:</b> Порывы ветра до <b>{gusts} м/с</b>! Высокий риск схлёстывания фазных проводов на столбах и скачка 380V. <b>Выключите электрообогреватели из розеток на ночь!</b>"
        elif gusts >= 13:
            wire_alert = f"\n\n⚠️ <b>СИЛЬНЫЙ ВЕТЕР:</b> Порывы до <b>{gusts} м/с</b>, на улице раскачивает провода."
        else:
            wire_alert = f"\n\n⚡️ <b>Электросеть:</b> Безопасно. Порывы до {gusts} м/с. Провода стабильны."

        return (
            f"📍 <b>{location_name}</b> (высота {elevation:.0f} м)\n\n"
            f"🌡 <b>Температура:</b> {temp:+}°C (ощущается как {app:+}°C)\n"
            f"☁️ <b>Погода:</b> {cond}\n"
            f"🌧 <b>Шанс дождя сегодня:</b> {rain_prob}% ({rain_sum} мм)\n"
            f"💨 <b>Ветер:</b> {wind} м/с (порывы до {gusts} м/с)\n"
            f"💧 <b>Влажность:</b> {hum}% • <b>Давление:</b> {press_mm} мм рт. ст."
            f"{wire_alert}"
        )

def get_grid_safety_diagnostic(lang="ru"):
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=41.1465&longitude=22.5042"
        "&current=wind_speed_10m,wind_gusts_10m"
        "&daily=wind_gusts_10m_max&forecast_days=3&timezone=auto&wind_speed_unit=ms"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'BalkanMeteoBot/2.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return f"Error: {e}"

    cur_wind = round(data.get('current', {}).get('wind_speed_10m', 0), 1)
    daily_gusts = data.get('daily', {}).get('wind_gusts_10m_max', [0, 0, 0])
    gust_today = round(daily_gusts[0], 1)
    gust_tomorrow = round(daily_gusts[1], 1)

    if lang == "en":
        status_icon = "🟢" if gust_today < 13 else ("🟡" if gust_today < 17 else "🔴")
        status_text = "SAFE • NO DANGER" if gust_today < 13 else ("WARNING • STRONG GUSTS" if gust_today < 17 else "CRITICAL STORM HAZARD")
        advice = "Heaters & electronics can run normally. No risk of power line flapping." if gust_today < 13 else ("Wires will sway outside. If lights flicker, turn off high-power heaters." if gust_today < 17 else "High danger of wire galloping & phase surge! Unplug space heaters tonight!")
        return (
            f"⚡️ <b>POWER GRID SAFETY DIAGNOSTIC</b>\n"
            f"📍 <b>Location:</b> Bulevar Gevgelija 18\n\n"
            f"💨 <b>Current wind:</b> {cur_wind} m/s\n"
            f"🌪 <b>Max gusts today:</b> {gust_today} m/s\n"
            f"🌪 <b>Max gusts tomorrow:</b> {gust_tomorrow} m/s\n"
            f"⚠️ <b>Wire slapping hazard threshold:</b> 17.0 m/s\n\n"
            f"{status_icon} <b>STATUS: {status_text}</b>\n"
            f"{advice}"
        )
    else:
        status_icon = "🟢" if gust_today < 13 else ("🟡" if gust_today < 17 else "🔴")
        status_text = "БЕЗОПАСНО • СЕТЬ СПОКОЙНА" if gust_today < 13 else ("ВНИМАНИЕ • КРЕПКИЙ ВЕТЕР" if gust_today < 17 else "ШТОРМ • ОПАСНОСТЬ 380V")
        advice = "Обогреватели и техника работают штатно. Риск схлёстывания проводов на столбах отсутствует." if gust_today < 13 else ("Провода на улице будет раскачивать. При первых миганиях света отключите мощные приборы." if gust_today < 17 else "Высокий риск пляски проводов и межфазного замыкания 380V! Отключите обогреватель из розетки на ночь!")
        return (
            f"⚡️ <b>ДИАГНОСТИКА БЕЗОПАСНОСТИ ЭЛЕКТРОСЕТИ</b>\n"
            f"📍 <b>Точка:</b> Бульвар Гевгелия 18\n\n"
            f"💨 <b>Текущий ветер:</b> {cur_wind} м/с\n"
            f"🌪 <b>Макс. порывы сегодня:</b> {gust_today} м/с\n"
            f"🌪 <b>Макс. порывы завтра:</b> {gust_tomorrow} м/с\n"
            f"⚠️ <b>Порог схлёстывания проводов:</b> 17.0 м/с\n\n"
            f"{status_icon} <b>СТАТУС: {status_text}</b>\n"
            f"{advice}"
        )

def send_language_prompt(chat_id):
    """Initial onboarding prompt with the two inline buttons requested by the user"""
    text = (
        "🌐 <b>Вы говорите на каком языке? / What language do you speak?</b>\n\n"
        "Пожалуйста, выберите язык для работы с ботом:\n"
        "Please choose your language to continue:"
    )
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🇬🇧 English", "callback_data": "set_lang:en"},
                {"text": "🇷🇺 Русский", "callback_data": "set_lang:ru"}
            ]
        ]
    }
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    })

def send_main_menu(chat_id, lang):
    if lang == "en":
        text = (
            "Welcome to <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "• Tap <b>🌦 Open Meteo App</b> to launch the full-screen interactive station.\n"
            "• Tap <b>📍 Send Location</b> for real-time GPS elevation & micro-weather.\n"
            "• Tap <b>⚡️ Grid Safety</b> to check wind hazard for your heaters.\n"
            "• Tap <b>⚙️ Settings</b> anytime if you wish to change language."
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Open Meteo App", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Send Location (GPS)", "request_location": True}, {"text": "⚡️ Grid Safety"}],
                [{"text": "🏠 Gevgelija"}, {"text": "🏙 Skopje"}, {"text": "🌊 Ohrid"}],
                [{"text": "⚙️ Settings"}]
            ],
            "resize_keyboard": True
        }
    else:
        text = (
            "Добро пожаловать в <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "• Нажмите <b>🌦 Открыть метеостанцию</b> для запуска приложения на весь экран.\n"
            "• Нажмите <b>📍 Отправить геопозицию</b> для микроклимата по вашему GPS.\n"
            "• Нажмите <b>⚡️ Проверка сети</b> для диагностики риска для обогревателей.\n"
            "• Нажмите <b>⚙️ Настройки</b>, если захотите сменить язык."
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Открыть метеостанцию", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Отправить геопозицию (GPS)", "request_location": True}, {"text": "⚡️ Проверка сети"}],
                [{"text": "🏠 Гевгелия"}, {"text": "🏙 Скопье"}, {"text": "🌊 Охрид"}],
                [{"text": "⚙️ Настройки"}]
            ],
            "resize_keyboard": True
        }

    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    })

def send_settings_menu(chat_id, lang):
    title = (
        "⚙️ <b>Settings / Настройки</b>\n\n"
        "Current language / Текущий язык: <b>" + ("English 🇬🇧" if lang == "en" else "Русский 🇷🇺") + "</b>\n\n"
        "Choose new language / Выберите язык:"
    )
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🇬🇧 English", "callback_data": "set_lang:en"},
                {"text": "🇷🇺 Русский", "callback_data": "set_lang:ru"}
            ]
        ]
    }
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": title,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    })

def handle_callback_query(cq):
    cq_id = cq.get("id")
    from_user = cq.get("from", {})
    chat_id = from_user.get("id")
    data = cq.get("data", "")
    msg = cq.get("message", {})
    msg_id = msg.get("message_id")

    call_tg("answerCallbackQuery", {"callback_query_id": cq_id})

    if data.startswith("set_lang:"):
        lang = data.split(":")[1]
        save_user_language(chat_id, lang)
        
        # Friendly edit on the inline prompt
        confirm_text = "🇬🇧 <b>Language set to English!</b>" if lang == "en" else "🇷🇺 <b>Выбран русский язык!</b>"
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": confirm_text,
                "parse_mode": "HTML"
            })
        
        send_main_menu(chat_id, lang)

def handle_message(msg):
    chat_id = msg.get("chat", {}).get("id")
    if not chat_id:
        return

    user_lang = USER_LANGS.get(str(chat_id))

    # Location message
    if "location" in msg:
        lang = user_lang or "ru"
        loc = msg["location"]
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        rep = get_weather_report(lat, lon, "GPS Location" if lang=="en" else "Точка на карте", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

    text = msg.get("text", "").strip()

    # /start handler: ALWAYS prompt language on /start
    if text.startswith("/start"):
        send_language_prompt(chat_id)
        return

    lang = user_lang or "ru"

    if text in ["/help", "/menu"]:
        send_main_menu(chat_id, lang)
        return

    if text in ["⚙️ Settings", "⚙️ Настройки", "/settings", "/lang"]:
        send_settings_menu(chat_id, lang)
        return

    if text in ["/app", "🌦 Open Meteo App", "🌦 Открыть метеостанцию"]:
        btn_text = "Launch Web App" if lang=="en" else "Запустить приложение"
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": "👇 Click the button to launch the full-screen interactive station:" if lang=="en" else "👇 Нажмите кнопку ниже, чтобы открыть интерактивное приложение:",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": f"🌦 {btn_text}", "web_app": {"url": WEB_APP_URL}}]
                ]
            }
        })
        return

    if text in ["/storm", "⚡️ Grid Safety", "⚡️ Проверка сети"]:
        diag = get_grid_safety_diagnostic(lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": diag, "parse_mode": "HTML"})
        return

    if text in ["/weather", "🏠 Gevgelija", "🏠 Гевгелия", "гевгелия", "gevgelija"]:
        rep = get_weather_report(41.1465, 22.5042, "Gevgelija (Bulevar 18)" if lang=="en" else "Гевгелия (Бульвар 18)", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

    if text in ["🏙 Skopje", "🏙 Скопье", "скопье", "skopje"]:
        rep = get_weather_report(41.9981, 21.4254, "Skopje Valley" if lang=="en" else "Скопье (Котловина)", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

    if text in ["🌊 Ohrid", "🌊 Охрид", "охрид", "ohrid"]:
        rep = get_weather_report(41.1128, 20.8019, "Ohrid Lakefront" if lang=="en" else "Охрид (Озеро)", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

    # Fallback to geocoding for any city in the world
    encoded = urllib.parse.quote(text)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&format=json"
    try:
        req = urllib.request.Request(geo_url, headers={'User-Agent': 'BalkanMeteoBot/2.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            geo_data = json.loads(resp.read().decode('utf-8'))
            results = geo_data.get('results', [])
            if results:
                r = results[0]
                rep = get_weather_report(r['latitude'], r['longitude'], f"{r['name']}, {r.get('country','')}", lang)
                call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
                return
    except Exception:
        pass

    fallback_msg = "Command not recognized. Tap /app or choose from the menu." if lang=="en" else "Команда не распознана. Нажмите /app или выберите кнопку в меню."
    call_tg("sendMessage", {"chat_id": chat_id, "text": fallback_msg})

def run_loop():
    print("Bot polling started with Language Onboarding for @macedonia_meteo_bot...")
    offset = 0
    while True:
        try:
            res = call_tg("getUpdates", {"offset": offset, "timeout": 25})
            if res and res.get("ok"):
                for upd in res.get("result", []):
                    offset = upd["update_id"] + 1
                    if "callback_query" in upd:
                        handle_callback_query(upd["callback_query"])
                    elif "message" in upd:
                        handle_message(upd["message"])
            time.sleep(0.5)
        except Exception as e:
            print(f"Polling loop exception: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_loop()
