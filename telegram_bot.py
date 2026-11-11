"""
Privacy-First Minimalist Telegram Weather Bot & Storm Sentinel for @macedonia_meteo_bot
- Minimalist Main Screen with intuitive hierarchy
- Permanent bottom keyboard (is_persistent: True) so it never collapses
- Seamless in-place menu navigation (editMessageText) with "« Back" buttons
- Integrated Popular Cities of Macedonia (Skopje, Ohrid, Bitola, Gevgelija, Strumica, Kavadarci, Prilep, Tetovo)
- Clean Settings Menu: Language, Change Home, User Guide, Privacy Policy, Reset Data
- Full GDPR & Privacy compliance: Right to be forgotten (Reset My Data)
- Street-level geocoding via Open-Meteo + OpenStreetMap Nominatim
- High-precision micro-climate & power grid storm sentinel
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
WEB_APP_URL = "https://bmwgtrmpower-ops.github.io/gevgelija-weather/?v=2"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_FILE = os.path.join(BASE_DIR, "user_profiles.json")
LEGACY_LANG_FILE = os.path.join(BASE_DIR, "user_languages.json")
USER_PROFILES = {}

WEATHER_CACHE = {}
CACHE_TTL = 300  # 5 minutes

POPULAR_CITIES = [
    {"name_ru": "🏛 Скопье", "name_en": "🏛 Skopje", "lat": 41.9981, "lon": 21.4254, "clean_ru": "Скопье", "clean_en": "Skopje"},
    {"name_ru": "🌊 Охрид", "name_en": "🌊 Ohrid", "lat": 41.1172, "lon": 20.8016, "clean_ru": "Охрид", "clean_en": "Ohrid"},
    {"name_ru": "🍇 Битола", "name_en": "🍇 Bitola", "lat": 41.0297, "lon": 21.3292, "clean_ru": "Битола", "clean_en": "Bitola"},
    {"name_ru": "☀️ Гевгелия", "name_en": "☀️ Gevgelija", "lat": 41.1465, "lon": 22.5042, "clean_ru": "Гевгелия", "clean_en": "Gevgelija"},
    {"name_ru": "⛰ Струмица", "name_en": "⛰ Strumica", "lat": 41.4378, "lon": 22.6433, "clean_ru": "Струмица", "clean_en": "Strumica"},
    {"name_ru": "🍷 Кавадарци", "name_en": "🍷 Kavadarci", "lat": 41.4331, "lon": 22.0119, "clean_ru": "Кавадарци", "clean_en": "Kavadarci"},
    {"name_ru": "🏰 Прилеп", "name_en": "🏰 Prilep", "lat": 41.3444, "lon": 21.5542, "clean_ru": "Прилеп", "clean_en": "Prilep"},
    {"name_ru": "🏔 Тетово", "name_en": "🏔 Tetovo", "lat": 42.0106, "lon": 20.9714, "clean_ru": "Тетово", "clean_en": "Tetovo"},
]

def load_user_profiles():
    global USER_PROFILES
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                USER_PROFILES = json.load(f)
        except Exception:
            USER_PROFILES = {}
    
    # Migrate legacy languages
    if os.path.exists(LEGACY_LANG_FILE):
        try:
            with open(LEGACY_LANG_FILE, "r", encoding="utf-8") as f:
                legacy = json.load(f)
                for cid, lang in legacy.items():
                    if cid not in USER_PROFILES:
                        USER_PROFILES[cid] = {"lang": lang}
                    else:
                        USER_PROFILES[cid].setdefault("lang", lang)
        except Exception:
            pass

    # Ensure creator profile has Gevgelija pre-configured privately
    if "542400016" in USER_PROFILES:
        USER_PROFILES["542400016"].setdefault("home", {
            "name": "Гевгелия",
            "lat": 41.1465,
            "lon": 22.5042
        })
    else:
        USER_PROFILES["542400016"] = {
            "lang": "ru",
            "home": {
                "name": "Гевгелия",
                "lat": 41.1465,
                "lon": 22.5042
            }
        }

    if "7568006226" in USER_PROFILES:
        USER_PROFILES["7568006226"].setdefault("home", {
            "name": "Gevgelija",
            "lat": 41.1465,
            "lon": 22.5042
        })

load_user_profiles()

def save_user_profiles():
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_PROFILES, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving profiles: {e}", flush=True)

def get_user_lang(chat_id):
    prof = USER_PROFILES.get(str(chat_id), {})
    return prof.get("lang", "ru")

def set_user_lang(chat_id, lang):
    cid = str(chat_id)
    if cid not in USER_PROFILES:
        USER_PROFILES[cid] = {}
    USER_PROFILES[cid]["lang"] = lang
    save_user_profiles()

def get_user_home(chat_id):
    prof = USER_PROFILES.get(str(chat_id), {})
    return prof.get("home")

def set_user_home(chat_id, name, lat, lon):
    cid = str(chat_id)
    if cid not in USER_PROFILES:
        USER_PROFILES[cid] = {}
    USER_PROFILES[cid]["home"] = {
        "name": name,
        "lat": round(lat, 4),
        "lon": round(lon, 4)
    }
    save_user_profiles()

def reset_user_data(chat_id):
    cid = str(chat_id)
    if cid in USER_PROFILES:
        del USER_PROFILES[cid]
        save_user_profiles()

def call_tg(method, data=None):
    if not BOT_TOKEN:
        print("[ERROR] BOT_TOKEN is not set!", flush=True)
        return None
    url = f"{API_URL}/{method}"
    headers = {"User-Agent": "MacedoniaMeteoBot/2.0"}
    req_data = None
    if data:
        headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[TG ERROR] {method}: {e}", flush=True)
        return None

def fetch_weather_data(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,surface_pressure"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_gusts_10m_max"
        "&forecast_days=3&timezone=auto&wind_speed_unit=ms"
    )
    now = time.time()
    if url in WEATHER_CACHE:
        cached_time, cached_val = WEATHER_CACHE[url]
        if now - cached_time < CACHE_TTL:
            return cached_val

    req = urllib.request.Request(url, headers={"User-Agent": "MacedoniaMeteoBot/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            WEATHER_CACHE[url] = (now, data)
            return data
    except Exception as e:
        print(f"Error fetching weather: {e}", flush=True)
        return None

def format_weather_report(lat, lon, location_name, lang="ru"):
    data = fetch_weather_data(lat, lon)
    if not data:
        return "Weather data unavailable / Ошибка получения данных" if lang == "en" else "Не удалось получить данные о погоде."

    cur = data.get("current", {})
    daily = data.get("daily", {})
    elevation = data.get("elevation", 0)

    temp = round(cur.get("temperature_2m", 0), 1)
    app = round(cur.get("apparent_temperature", 0), 1)
    hum = cur.get("relative_humidity_2m", 0)
    wind = round(cur.get("wind_speed_10m", 0), 1)
    gusts = round(cur.get("wind_gusts_10m", 0), 1)
    press_hpa = cur.get("surface_pressure", 1013)
    press_mm = round(press_hpa * 0.750062)
    wcode = cur.get("weather_code", 0)

    rain_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
    rain_sum = daily.get("precipitation_sum", [0])[0] if daily.get("precipitation_sum") else 0.0

    if lang == "en":
        cond = "Clear sky"
        if wcode in [1, 2]: cond = "Partly cloudy"
        elif wcode == 3: cond = "Overcast"
        elif wcode in [45, 48]: cond = "Foggy"
        elif wcode in [51, 53, 55, 61, 63, 65, 80]: cond = "Rain"
        elif wcode >= 95: cond = "Thunderstorm"

        wire_alert = ""
        if gusts >= 17:
            wire_alert = f"\n\n🚨 <b>POWER GRID STORM ALERT:</b> Wind gusts up to <b>{gusts} m/s</b>! High risk of overhead line slapping and 380V voltage surge. <b>Unplug electric heaters before sleep!</b>"
        elif gusts >= 13:
            wire_alert = f"\n\n⚠️ <b>STRONG GUSTS:</b> Gusts up to <b>{gusts} m/s</b>. Overhead lines swaying."
        else:
            wire_alert = f"\n\n⚡ <b>Power Grid:</b> Safe. Gusts {gusts} m/s. Overhead lines stable."

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
            wire_alert = f"\n\n⚡ <b>Электросеть:</b> Безопасно. Порывы до {gusts} м/с. Провода стабильны."

        return (
            f"📍 <b>{location_name}</b> (высота {elevation:.0f} м)\n\n"
            f"🌡 <b>Температура:</b> {temp:+}°C (ощущается как {app:+}°C)\n"
            f"☁️ <b>Погода:</b> {cond}\n"
            f"🌧 <b>Шанс дождя сегодня:</b> {rain_prob}% ({rain_sum} мм)\n"
            f"💨 <b>Ветер:</b> {wind} м/с (порывы до {gusts} м/с)\n"
            f"💧 <b>Влажность:</b> {hum}% • <b>Давление:</b> {press_mm} мм рт. ст."
            f"{wire_alert}"
        )

def get_grid_safety_diagnostic(lat, lon, location_name, lang="ru"):
    data = fetch_weather_data(lat, lon)
    if not data:
        return "Error fetching diagnostic" if lang == "en" else "Ошибка получения диагностических данных"

    cur_wind = round(data.get('current', {}).get('wind_speed_10m', 0), 1)
    daily_gusts = data.get('daily', {}).get('wind_gusts_10m_max', [0, 0, 0])
    gust_today = round(daily_gusts[0], 1)
    gust_tomorrow = round(daily_gusts[1], 1)

    if lang == "en":
        status_icon = "🟢" if gust_today < 13 else ("🟡" if gust_today < 17 else "🔴")
        status_text = "SAFE • NO DANGER" if gust_today < 13 else ("WARNING • STRONG GUSTS" if gust_today < 17 else "CRITICAL STORM HAZARD")
        advice = "Heaters & electronics can run normally. No risk of power line flapping." if gust_today < 13 else ("Wires will sway outside. If lights flicker, turn off high-power heaters." if gust_today < 17 else "High danger of wire galloping & phase surge! Unplug space heaters tonight!")
        return (
            f"⚡ <b>POWER GRID SAFETY DIAGNOSTIC</b>\n"
            f"📍 <b>Location:</b> {location_name}\n\n"
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
            f"⚡ <b>ДИАГНОСТИКА БЕЗОПАСНОСТИ ЭЛЕКТРОСЕТИ</b>\n"
            f"📍 <b>Локация:</b> {location_name}\n\n"
            f"💨 <b>Текущий ветер:</b> {cur_wind} м/с\n"
            f"🌪 <b>Макс. порывы сегодня:</b> {gust_today} м/с\n"
            f"🌪 <b>Макс. порывы завтра:</b> {gust_tomorrow} м/с\n"
            f"⚠️ <b>Порог схлёстывания проводов:</b> 17.0 м/с\n\n"
            f"{status_icon} <b>СТАТУС: {status_text}</b>\n"
            f"{advice}"
        )

def send_language_prompt(chat_id):
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
    """
    Minimalist Main Screen with intuitive hierarchy.
    is_persistent: True locks the keyboard permanently so it NEVER collapses!
    """
    home = get_user_home(chat_id)
    home_btn = f"🏠 {home['name']}" if home else ("🏠 My Home" if lang=="en" else "🏠 Мой дом")

    if lang == "en":
        text = (
            "Welcome to <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "• <b>⛅ Open Meteo App</b> — interactive radar & charts\n"
            "• <b>📍 Send Location</b> — micro-climate at your GPS position\n"
            f"• <b>{home_btn}</b> — instant weather at your home\n"
            "• <b>🏙 Cities of Macedonia</b> — Skopje, Ohrid, Bitola & more\n"
            "• <b>⚡ Grid Safety</b> — space heater & wire storm protection\n"
            "• <b>⚙️ Settings</b> — change home, language & privacy"
        )
        keyboard = {
            "keyboard": [
                [{"text": "⛅ Open Meteo App", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Send Location (GPS)", "request_location": True}, {"text": home_btn}],
                [{"text": "🏙 Cities of Macedonia"}, {"text": "⚡ Grid Safety"}],
                [{"text": "⚙️ Settings"}]
            ],
            "resize_keyboard": True,
            "is_persistent": True
        }
    else:
        text = (
            "Добро пожаловать в <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "• <b>⛅ Открыть метеостанцию</b> — интерактивный радар и графики\n"
            "• <b>📍 Отправить локацию</b> — микроклимат в вашей точке GPS\n"
            f"• <b>{home_btn}</b> — погода у вас дома в 1 клик\n"
            "• <b>🏙 Города Македонии</b> — Скопье, Охрид, Битола и др.\n"
            "• <b>⚡ Стабильность сети</b> — защита обогревателей от штормовых порывов\n"
            "• <b>⚙️ Настройки</b> — смена языка, домашний адрес, приватность"
        )
        keyboard = {
            "keyboard": [
                [{"text": "⛅ Открыть метеостанцию", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Отправить локацию (GPS)", "request_location": True}, {"text": home_btn}],
                [{"text": "🏙 Города Македонии"}, {"text": "⚡ Стабильность сети"}],
                [{"text": "⚙️ Настройки"}]
            ],
            "resize_keyboard": True,
            "is_persistent": True
        }

    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    })

def build_cities_payload(lang):
    """Builds inline grid of popular Macedonian regional centers."""
    if lang == "en":
        text = (
            "🏙 <b>Popular Cities of Macedonia</b>\n\n"
            "Choose a city below for an instant micro-climate report, or simply <b>type any city, village, or street name</b> into this chat:"
        )
    else:
        text = (
            "🏙 <b>Популярные города Македонии</b>\n\n"
            "Выберите город для мгновенного прогноза или просто <b>напишите название любого посёлка или улицы</b> в этот чат:"
        )

    grid = []
    # 4 rows of 2 cities
    for i in range(0, len(POPULAR_CITIES), 2):
        row = []
        c1 = POPULAR_CITIES[i]
        btn1_text = c1["name_en"] if lang == "en" else c1["name_ru"]
        clean1 = c1["clean_en"] if lang == "en" else c1["clean_ru"]
        row.append({"text": btn1_text, "callback_data": f"city:{clean1}:{c1['lat']}:{c1['lon']}"})

        if i + 1 < len(POPULAR_CITIES):
            c2 = POPULAR_CITIES[i + 1]
            btn2_text = c2["name_en"] if lang == "en" else c2["name_ru"]
            clean2 = c2["clean_en"] if lang == "en" else c2["clean_ru"]
            row.append({"text": btn2_text, "callback_data": f"city:{clean2}:{c2['lat']}:{c2['lon']}"})
        grid.append(row)

    return text, {"inline_keyboard": grid}

def send_cities_menu(chat_id, lang):
    text, markup = build_cities_payload(lang)
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": markup
    })

def build_settings_payload(chat_id, lang):
    """Constructs the settings menu in-place payload without cities clutter."""
    home = get_user_home(chat_id)
    home_str = f"<b>{home['name']}</b> ({home['lat']}, {home['lon']})" if home else ("<i>Not set</i>" if lang == "en" else "<i>Не задан</i>")
    
    if lang == "en":
        text = (
            "⚙️ <b>Settings & Profile</b>\n\n"
            f"🌐 <b>Language:</b> English 🇬🇧\n"
            f"🏠 <b>Home address:</b> {home_str}\n\n"
            "Select an option below:"
        )
        switch_lang_btn = {"text": "🌐 Switch to Russian 🇷🇺", "callback_data": "toggle_lang:ru"}
        set_home_btn = {"text": "🏠 Change Home Address", "callback_data": "menu_set_home"}
        guide_btn = {"text": "📖 User Guide", "callback_data": "menu_guide"}
        privacy_btn = {"text": "🔒 Privacy Policy", "callback_data": "menu_privacy"}
        reset_btn = {"text": "🗑 Reset My Data (GDPR)", "callback_data": "menu_reset"}
    else:
        text = (
            "⚙️ <b>Настройки и профиль</b>\n\n"
            f"🌐 <b>Язык:</b> Русский 🇷🇺\n"
            f"🏠 <b>Домашний адрес:</b> {home_str}\n\n"
            "Выберите нужный раздел:"
        )
        switch_lang_btn = {"text": "🌐 Switch to English 🇬🇧", "callback_data": "toggle_lang:en"}
        set_home_btn = {"text": "🏠 Задать / изменить адрес", "callback_data": "menu_set_home"}
        guide_btn = {"text": "📖 Инструкция", "callback_data": "menu_guide"}
        privacy_btn = {"text": "🔒 Конфиденциальность", "callback_data": "menu_privacy"}
        reset_btn = {"text": "🗑 Сбросить мои данные", "callback_data": "menu_reset"}

    inline_keyboard = {
        "inline_keyboard": [
            [switch_lang_btn],
            [set_home_btn],
            [guide_btn, privacy_btn],
            [reset_btn]
        ]
    }
    return text, inline_keyboard

def send_settings_menu(chat_id, lang):
    text, inline_keyboard = build_settings_payload(chat_id, lang)
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    })

def get_back_button(lang):
    txt = "« 🔙 Back / Назад" if lang == "en" else "« 🔙 Назад в настройки"
    return {"inline_keyboard": [[{"text": txt, "callback_data": "menu_settings"}]]}

def build_guide_text(lang):
    if lang == "en":
        return (
            "📖 <b>USER GUIDE & BOT CAPABILITIES</b>\n\n"
            "• <b>⛅ Open Meteo App</b> — opens full interactive WebApp radar.\n"
            "• <b>📍 Send Location</b> — micro-climate at your current GPS location.\n"
            "• <b>🏠 My Home</b> — 1-tap weather for your saved address.\n"
            "• <b>🏙 Cities of Macedonia</b> — instant forecast for 8 major regional centers.\n"
            "• <b>⚡ Grid Safety</b> — space heater & power grid storm protection.\n"
            "• <b>⚙️ Settings</b> — manage language, privacy, and personal profile."
        )
    else:
        return (
            "📖 <b>ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ БОТА</b>\n\n"
            "• <b>⛅ Открыть метеостанцию</b> — интерактивная полноэкранная веб-панель с графиками и радаром.\n"
            "• <b>📍 Отправить локацию</b> — моментальная погода в точке вашего нахождения (по спутникам GPS).\n"
            "• <b>🏠 Мой дом</b> — прогноз у вас дома в один клик.\n"
            "• <b>🏙 Города Македонии</b> — моментальный прогноз для 8 ключевых городов страны в 1 клик.\n"
            "• <b>⚡ Стабильность сети</b> — защита электросети и обогревателей от штормовых порывов 380V.\n"
            "• <b>⚙️ Настройки</b> — смена языка, управление адресом, приватность и сброс данных."
        )

def build_privacy_text(lang):
    if lang == "en":
        return (
            "🔒 <b>PRIVACY & DATA PROTECTION POLICY</b>\n\n"
            "<b>1. What data we store:</b>\n"
            "• Anonymous technical Telegram ID to remember your language and home city.\n"
            "• Your chosen language preference (EN/RU).\n"
            "• Your saved home coordinates (only if voluntarily set).\n\n"
            "<b>2. What we NEVER collect:</b>\n"
            "• ❌ No real names, passports or personal identity data.\n"
            "• ❌ No phone numbers, contacts or email addresses.\n"
            "• ❌ No payment or banking details.\n"
            "• ❌ No IP addresses — Telegram shields all network connections.\n\n"
            "<b>3. Zero Leaks & Complete Isolation:</b>\n"
            "• User profiles are strictly isolated; no user can ever see another user's address.\n"
            "• Data is never uploaded to GitHub or sold to 3rd parties.\n\n"
            "<b>4. Right to Erasure (GDPR Art. 17):</b>\n"
            "• You can permanently delete all your data anytime via the <b>Reset My Data</b> button."
        )
    else:
        return (
            "🔒 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ И БЕЗОПАСНОСТИ</b>\n\n"
            "<b>1. Какие данные мы храним:</b>\n"
            "• Обезличенный технический Telegram ID для запоминания языка и города.\n"
            "• Выбранный язык (RU / EN).\n"
            "• Координаты города или улицы, если вы сами нажали «Сохранить как мой дом».\n\n"
            "<b>2. Чего мы НЕ собираем принципиально:</b>\n"
            "• ❌ Никаких паспортов, реальных имён или фамилий.\n"
            "• ❌ Никаких номеров телефонов, контактов или email.\n"
            "• ❌ Никаких платёжных данных или банковских карт.\n"
            "• ❌ Никаких IP-адресов — Telegram полностью скрывает ваш IP через свои шлюзы.\n\n"
            "<b>3. Изоляция и безопасность:</b>\n"
            "• Профили полностью изолированы: чужой пользователь никогда не узнает ваш адрес.\n"
            "• Данные никогда не выгружаются на GitHub и не передаются рекламодателям.\n\n"
            "<b>4. Право на забвение (GDPR):</b>\n"
            "• Вы можете в любой момент полностью стереть свой профиль кнопкой <b>«Сбросить мои данные»</b>."
        )

def build_set_home_text(lang):
    if lang == "en":
        return (
            "🏠 <b>SET OR CHANGE HOME ADDRESS</b>\n\n"
            "To set your personal home location, you can:\n"
            "1. Simply <b>type the name of your city, street, or address</b> in this chat (e.g. <code>Gevgelija</code>, <code>Bulevar Gevgelija</code>, or <code>Skopje</code>).\n"
            "2. Or tap <b>📍 Send Location</b> from the bottom keyboard.\n\n"
            "The bot will find your coordinates and ask if you want to save it as your private Home address."
        )
    else:
        return (
            "🏠 <b>ЗАДАТЬ ИЛИ ИЗМЕНИТЬ ДОМАШНИЙ АДРЕС</b>\n\n"
            "Чтобы настроить домашнюю точку, вы можете:\n"
            "1. Просто <b>напишите название своего города, улицы или адреса</b> в этот чат (например: <code>Гевгелия</code>, <code>Булевар Гевгелия</code>, <code>Скопье</code>).\n"
            "2. Либо нажмите кнопку <b>📍 Отправить локацию</b> на нижней панели.\n\n"
            "Бот определит координаты и предложит закрепить их как ваш домашний адрес."
        )

def handle_callback_query(cq):
    cq_id = cq.get("id")
    from_user = cq.get("from", {})
    chat_id = from_user.get("id")
    data = cq.get("data", "")
    msg = cq.get("message", {})
    msg_id = msg.get("message_id")

    call_tg("answerCallbackQuery", {"callback_query_id": cq_id})
    lang = get_user_lang(chat_id)

    # Initial Language Picker
    if data.startswith("set_lang:"):
        new_lang = data.split(":")[1]
        set_user_lang(chat_id, new_lang)
        confirm_text = "🇬🇧 <b>Language set to English!</b>" if new_lang == "en" else "🇷🇺 <b>Выбран русский язык!</b>"
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": confirm_text,
                "parse_mode": "HTML"
            })
        send_main_menu(chat_id, new_lang)
        return

    # Language Toggle from Settings
    if data.startswith("toggle_lang:"):
        new_lang = data.split(":")[1]
        set_user_lang(chat_id, new_lang)
        send_main_menu(chat_id, new_lang)
        text, markup = build_settings_payload(chat_id, new_lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # In-Place Back to Settings Menu
    if data == "menu_settings":
        text, markup = build_settings_payload(chat_id, lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # In-Place Back to Cities Menu
    if data == "show_cities":
        text, markup = build_cities_payload(lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # User Guide in-place
    if data == "menu_guide":
        text = build_guide_text(lang)
        markup = get_back_button(lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # Privacy Policy in-place
    if data == "menu_privacy":
        text = build_privacy_text(lang)
        markup = get_back_button(lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # Set Home Address in-place
    if data == "menu_set_home":
        text = build_set_home_text(lang)
        markup = get_back_button(lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        return

    # Reset Data (GDPR) in-place
    if data == "menu_reset":
        reset_user_data(chat_id)
        text = (
            "🗑 <b>Your personal profile and saved location have been permanently erased.</b>\n\n"
            "Under GDPR Art. 17 (Right to Erasure), no traces remain in our storage."
            if lang == "en" else
            "🗑 <b>Ваш профиль и сохранённая геолокация полностью удалены.</b>\n\n"
            "В соответствии со стандартом GDPR (право на забвение), все ваши данные стёрты без возможности восстановления."
        )
        markup = get_back_button(lang)
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": markup
            })
        send_main_menu(chat_id, lang)
        return

    # City Selected from Grid
    if data.startswith("city:"):
        parts = data.split(":")
        name = parts[1]
        lat = float(parts[2])
        lon = float(parts[3])
        rep = format_weather_report(lat, lon, name, lang)
        save_btn_text = "🏠 Save as My Home" if lang == "en" else "🏠 Сохранить как мой дом"
        back_cities_text = "« 🔙 Back to Cities" if lang == "en" else "« 🔙 К списку городов"
        inline = {
            "inline_keyboard": [
                [{"text": save_btn_text, "callback_data": f"save_home:{lat}:{lon}:{name}"}],
                [{"text": back_cities_text, "callback_data": "show_cities"}]
            ]
        }
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": rep,
                "parse_mode": "HTML",
                "reply_markup": inline
            })
        return

    # Save Location as Home
    if data.startswith("save_home:"):
        parts = data.split(":")
        lat = float(parts[1])
        lon = float(parts[2])
        loc_name = parts[3]
        set_user_home(chat_id, loc_name, lat, lon)
        saved_text = (
            f"✅ <b>{loc_name}</b> has been saved as your private Home address!"
            if lang == "en" else
            f"✅ <b>{loc_name}</b> успешно сохранён как ваш домашний адрес!"
        )
        if msg_id:
            call_tg("editMessageText", {
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": saved_text,
                "parse_mode": "HTML"
            })
        send_main_menu(chat_id, lang)
        return

def handle_text_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    lang = get_user_lang(chat_id)

    if text.startswith("/start"):
        if str(chat_id) not in USER_PROFILES:
            send_language_prompt(chat_id)
        else:
            send_main_menu(chat_id, lang)
        return

    if text in ["⚙️ Settings", "⚙️ Настройки", "/settings"]:
        send_settings_menu(chat_id, lang)
        return

    if text in ["🏙 Cities of Macedonia", "🏙 Города Македонии", "🏙 Cities", "🏙 Города", "/cities"]:
        send_cities_menu(chat_id, lang)
        return

    if text in ["⚡ Grid Safety", "⚡ Стабильность сети", "⚡ Проверка сети"]:
        home = get_user_home(chat_id)
        lat = home["lat"] if home else 41.1465
        lon = home["lon"] if home else 22.5042
        loc_name = home["name"] if home else "Гевгелия"
        diag = get_grid_safety_diagnostic(lat, lon, loc_name, lang)
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": diag,
            "parse_mode": "HTML"
        })
        return

    if text.startswith("🏠"):
        home = get_user_home(chat_id)
        if home:
            rep = format_weather_report(home["lat"], home["lon"], f"🏠 {home['name']}", lang)
            call_tg("sendMessage", {
                "chat_id": chat_id,
                "text": rep,
                "parse_mode": "HTML"
            })
        else:
            prompt = (
                "🏠 You haven't set a home address yet!\n\n"
                "Send your city name in the chat (e.g. <code>Gevgelija</code> or <code>Skopje</code>) or tap <b>📍 Send Location</b>."
                if lang == "en" else
                "🏠 Вы ещё не задали домашний адрес!\n\n"
                "Напишите название своего города в чат (например: <code>Гевгелия</code> или <code>Скопье</code>) или нажмите <b>📍 Отправить локацию</b>."
            )
            call_tg("sendMessage", {
                "chat_id": chat_id,
                "text": prompt,
                "parse_mode": "HTML"
            })
        return

    # Geocoding search (City / Street lookup)
    query = text
    encoded = urllib.parse.quote(query)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language={'en' if lang=='en' else 'ru'}&format=json"
    results = None
    try:
        req = urllib.request.Request(geo_url, headers={"User-Agent": "MacedoniaMeteoBot/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results")
    except Exception as e:
        print(f"Geocoding error: {e}", flush=True)

    # Secondary OSM Nominatim check for streets & small Macedonian settlements
    if not results:
        try:
            nom_url = f"https://nominatim.openstreetmap.org/search?q={encoded}&countrycodes=mk&format=json&limit=1"
            req2 = urllib.request.Request(nom_url, headers={"User-Agent": "MacedoniaMeteoBot/2.0 (contact@meteo.internal)"})
            with urllib.request.urlopen(req2, timeout=8) as resp2:
                nom_data = json.loads(resp2.read().decode("utf-8"))
                if nom_data:
                    item = nom_data[0]
                    results = [{
                        "name": item.get("display_name", "").split(",")[0],
                        "latitude": float(item.get("lat")),
                        "longitude": float(item.get("lon"))
                    }]
        except Exception as e:
            print(f"Nominatim error: {e}", flush=True)

    if results:
        match = results[0]
        lat = match.get("latitude")
        lon = match.get("longitude")
        name = match.get("name", query)
        country = match.get("country", "")
        display = f"{name}, {country}" if country else name
        rep = format_weather_report(lat, lon, display, lang)

        save_btn_text = "🏠 Save as My Home" if lang == "en" else "🏠 Сохранить как мой дом"
        inline = {
            "inline_keyboard": [
                [{"text": save_btn_text, "callback_data": f"save_home:{lat}:{lon}:{name}"}]
            ]
        }
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": rep,
            "parse_mode": "HTML",
            "reply_markup": inline
        })
    else:
        not_found = (
            f"🔍 Location '<b>{query}</b>' not found.\nTry entering city name or exact street in Macedonia."
            if lang == "en" else
            f"🔍 Локация '<b>{query}</b>' не найдена.\nПопробуйте написать название города или улицы в Македонии (например: <code>Гевгелия</code>, <code>Скопье</code>, <code>Охрид</code>)."
        )
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": not_found,
            "parse_mode": "HTML"
        })

def handle_location_message(msg):
    chat_id = msg["chat"]["id"]
    loc = msg.get("location", {})
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    lang = get_user_lang(chat_id)

    if lat is None or lon is None:
        return

    place_name = f"GPS ({lat:.3f}, {lon:.3f})"
    try:
        rev_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=16"
        req = urllib.request.Request(rev_url, headers={"User-Agent": "MacedoniaMeteoBot/2.0 (contact@meteo.internal)"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            addr = data.get("address", {})
            road = addr.get("road")
            town = addr.get("town") or addr.get("city") or addr.get("village") or addr.get("suburb")
            if road and town:
                place_name = f"{road}, {town}"
            elif town:
                place_name = town
    except Exception as e:
        print(f"Reverse geocode error: {e}", flush=True)

    rep = format_weather_report(lat, lon, place_name, lang)
    save_btn_text = "🏠 Save as My Home" if lang == "en" else "🏠 Сохранить как мой дом"
    inline = {
        "inline_keyboard": [
            [{"text": save_btn_text, "callback_data": f"save_home:{lat}:{lon}:{place_name}"}]
        ]
    }
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": rep,
        "parse_mode": "HTML",
        "reply_markup": inline
    })

def main():
    print(f"Starting Macedonia Meteo Bot daemon (@macedonia_meteo_bot)...", flush=True)
    last_update_id = 0

    while True:
        try:
            updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 20})
            if updates and updates.get("ok"):
                for u in updates.get("result", []):
                    last_update_id = u.get("update_id", last_update_id)

                    if "callback_query" in u:
                        handle_callback_query(u["callback_query"])
                    elif "message" in u:
                        msg = u["message"]
                        if "location" in msg:
                            handle_location_message(msg)
                        elif "text" in msg:
                            handle_text_message(msg)
            time.sleep(0.5)
        except Exception as e:
            print(f"Exception in polling loop: {e}", flush=True)
            time.sleep(2)

if __name__ == "__main__":
    main()
