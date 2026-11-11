"""
Privacy-First Bilingual Telegram Weather Bot & Storm Sentinel for @macedonia_meteo_bot
- Full confidentiality: each user has an isolated profile (home location, coordinates, language)
- No personal street addresses ("Bulevar 18", etc.) are exposed to public users
- Personal Home Location ("🏠 Мой дом / 🏠 My Home") customizable per user
- Quick Popular Cities menu (Skopje, Ohrid, Bitola, Strumica, Mavrovo, Kavadarci)
- Full User Guide & Privacy Guarantee ("📖 Инструкция / 📖 User Guide")
- Interactive Telegram Mini App integration
- Power Grid Storm Sentinel (wind gusts & wire galloping protection)
- Capacity: can easily support hundreds of users with 0 server costs
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys
import uuid

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

# In-memory weather cache (url -> (timestamp, data)) to protect Open-Meteo limits
WEATHER_CACHE = {}
CACHE_TTL = 300 # 5 minutes

def load_user_profiles():
    global USER_PROFILES
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                USER_PROFILES = json.load(f)
        except Exception:
            USER_PROFILES = {}
    
    # Migrate legacy languages file if needed
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

    # Ensure owner/creator has Gevgelija pre-configured as home privately
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

def save_user_profiles():
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_PROFILES, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving profiles: {e}", flush=True)

load_user_profiles()

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
        cached_time, cached_data = WEATHER_CACHE[url]
        if now - cached_time < CACHE_TTL:
            return cached_data

    req = urllib.request.Request(url, headers={'User-Agent': 'BalkanMeteoBot/2.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            WEATHER_CACHE[url] = (now, data)
            return data
    except Exception as e:
        print(f"Fetch error: {e}", flush=True)
        return None

def get_weather_report(lat, lon, location_name, lang="ru"):
    data = fetch_weather_data(lat, lon)
    if not data:
        return "Service temporarily unavailable / Сервис временно недоступен"

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

def get_grid_safety_diagnostic(lat, lon, location_name, lang="ru"):
    data = fetch_weather_data(lat, lon)
    if not data:
        return "Error fetching diagnostic"

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
            f"⚡️ <b>ДИАГНОСТИКА БЕЗОПАСНОСТИ ЭЛЕКТРОСЕТИ</b>\n"
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
    home = get_user_home(chat_id)
    home_btn = f"🏠 {home['name']}" if home else ("🏠 Set My Home" if lang=="en" else "🏠 Задать мой дом")

    if lang == "en":
        text = (
            "Welcome to <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "✨ <b>Quick Actions:</b>\n"
            "• <b>🌦 Open Meteo App</b> — full-screen interactive dashboard\n"
            "• <b>📍 Send Location</b> — real-time micro-weather at your feet\n"
            f"• <b>{home_btn}</b> — quick weather at your personal address\n"
            "• <b>⚡️ Grid Safety</b> — space heater & power wire storm diagnostic\n"
            "• <b>🏙 Popular Cities</b> — Skopje, Ohrid, Bitola, Mavrovo...\n"
            "• <b>📖 User Guide</b> — full manual & privacy policy\n"
            "• <b>⚙️ Settings</b> — change language or home address"
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Open Meteo App", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Send Location (GPS)", "request_location": True}, {"text": home_btn}],
                [{"text": "⚡️ Grid Safety"}, {"text": "🏙 Popular Cities"}],
                [{"text": "📖 User Guide"}, {"text": "⚙️ Settings"}]
            ],
            "resize_keyboard": True
        }
    else:
        text = (
            "Добро пожаловать в <b>macedonia meteo bot</b> 🇲🇰\n\n"
            "✨ <b>Основные возможности:</b>\n"
            "• <b>🌦 Открыть метеостанцию</b> — интерактивное приложение на весь экран\n"
            "• <b>📍 Моя геопозиция</b> — погода прямо там, где вы находитесь\n"
            f"• <b>{home_btn}</b> — погода у вашего дома в один клик\n"
            "• <b>⚡️ Проверка сети</b> — диагностика ветра для защиты обогревателей\n"
            "• <b>🏙 Города Македонии</b> — Скопье, Охрид, Битола, Маврово...\n"
            "• <b>📖 Инструкция</b> — полное руководство и гарантия приватности\n"
            "• <b>⚙️ Настройки</b> — сменить язык или домашний адрес"
        )
        keyboard = {
            "keyboard": [
                [{"text": "🌦 Открыть метеостанцию", "web_app": {"url": WEB_APP_URL}}],
                [{"text": "📍 Моя геопозиция (GPS)", "request_location": True}, {"text": home_btn}],
                [{"text": "⚡️ Проверка сети"}, {"text": "🏙 Города Македонии"}],
                [{"text": "📖 Инструкция"}, {"text": "⚙️ Настройки"}]
            ],
            "resize_keyboard": True
        }

    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    })

def send_popular_cities(chat_id, lang):
    title = "🏙 <b>Select a city / Выберите город:</b>"
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🏙 Скопье / Skopje", "callback_data": "city:skopje"},
                {"text": "🌊 Охрид / Ohrid", "callback_data": "city:ohrid"}
            ],
            [
                {"text": "🏛 Битола / Bitola", "callback_data": "city:bitola"},
                {"text": "🍓 Струмица / Strumica", "callback_data": "city:strumica"}
            ],
            [
                {"text": "🍷 Кавадарци / Kavadarci", "callback_data": "city:kavadarci"},
                {"text": "🏔 Маврово / Mavrovo", "callback_data": "city:mavrovo"}
            ]
        ]
    }
    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": title,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    })

def send_user_guide(chat_id, lang):
    if lang == "en":
        guide = (
            "📖 <b>USER GUIDE & PRIVACY POLICY</b>\n\n"
            "<b>1. What makes this bot special:</b>\n"
            "• <b>Micro-Climate Precision:</b> High-resolution atmospheric forecast with actual elevation, air pressure in mmHg, feels-like temperature, and exact rain probability.\n"
            "• <b>⚡️ Power Grid Sentinel:</b> Automatically checks wind gusts for wire galloping risk. If gusts exceed 17 m/s, it warns you to unplug electric space heaters to prevent 380V phase-slapping surges.\n\n"
            "<b>2. 🔒 Privacy Guarantee:</b>\n"
            "• Each user's data is strictly isolated. Nobody else can see where you live or your saved location.\n"
            "• There are no public personal addresses or streets shown in the bot.\n\n"
            "<b>3. How to set your Home Address:</b>\n"
            "• Tap <b>📍 Send Location (GPS)</b> or type any city name in chat (e.g. <i>Bitola</i> or <i>Gevgelija</i>).\n"
            "• Tap the <b>📌 Save as My Home</b> button under the forecast.\n"
            "• From now on, tap <b>🏠 My Home</b> anytime for instant local weather!\n\n"
            "<b>4. Free Forever & Capacity:</b>\n"
            "• Built on serverless public APIs and GitHub CDN — 100% free, 0 maintenance, capable of serving hundreds of daily users."
        )
    else:
        guide = (
            "📖 <b>РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ И КОНФИДЕНЦИАЛЬНОСТЬ</b>\n\n"
            "<b>1. Чем уникален этот бот:</b>\n"
            "• <b>Сверхточный микроклимат:</b> Прогноз с учётом высоты над уровнем моря, атмосферного давления в мм рт. ст., ощущаемой температуры и точной вероятности дождя в процентах.\n"
            "• <b>⚡️ Защита электросети и обогревателей:</b> Умный алгоритм анализирует порывы ветра. При штормовом ветре (от 17 м/с) бот предупреждает об опасности схлёстывания фазных проводов на столбах и рекомендует отключить электрообогреватели от розеток на ночь, чтобы спасти технику от скачка 380V.\n\n"
            "<b>2. 🔒 Конфиденциальность (Privacy):</b>\n"
            "• Профиль каждого пользователя полностью изолирован. Никто другой не знает и не увидит, где вы находитесь или где живёте.\n"
            "• В боте нет публичных домашних адресов или улиц создателя — все видят только свои данные и общие города.\n\n"
            "<b>3. Как настроить «Мой дом»:</b>\n"
            "• Нажмите <b>📍 Моя геопозиция (GPS)</b> или просто напишите в чат любой город (например: <i>Битола</i>, <i>Гевгелия</i>, <i>Скопье</i>).\n"
            "• Под появившейся сводкой нажмите кнопку <b>📌 Сохранить как мой дом</b>.\n"
            "• Теперь кнопка <b>🏠 Мой дом</b> всегда будет показывать погоду у вас дома в один клик!\n\n"
            "<b>4. Надёжность и лимиты:</b>\n"
            "• Бот и Mini App работают на бессерверной инфраструктуре и выдерживают сотни активных пользователей без сбоев."
        )

    call_tg("sendMessage", {
        "chat_id": chat_id,
        "text": guide,
        "parse_mode": "HTML"
    })

def send_settings_menu(chat_id, lang):
    home = get_user_home(chat_id)
    home_name = home["name"] if home else ("Not set / Не задан")
    
    title = (
        "⚙️ <b>Settings / Настройки</b>\n\n"
        f"🌐 Current language / Язык: <b>{'English 🇬🇧' if lang=='en' else 'Русский 🇷🇺'}</b>\n"
        f"🏠 Home location / Домашний адрес: <b>{home_name}</b>\n\n"
        "Choose an action / Выберите действие:"
    )
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🇬🇧 English", "callback_data": "set_lang:en"},
                {"text": "🇷🇺 Русский", "callback_data": "set_lang:ru"}
            ],
            [
                {"text": "🏠 " + ("Set/Change Home Address" if lang=="en" else "Задать/Сменить домашний адрес"), "callback_data": "prompt_set_home"}
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
    lang = get_user_lang(chat_id)

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

    if data == "prompt_set_home":
        prompt = (
            "📍 <b>How to set your Home Address:</b>\n\n"
            "1. Tap the <b>📎 Attachment icon</b> and share your Location (GPS).\n"
            "2. OR type your town/city name directly into chat (e.g. <i>Skopje</i>, <i>Bitola</i>, <i>Gevgelija</i>).\n"
            "3. Then tap the <b>📌 Save as My Home</b> button under the result.\n\n"
            "🔒 <i>Your location remains strictly confidential in your private profile.</i>"
        ) if lang == "en" else (
            "📍 <b>Как сохранить домашний адрес:</b>\n\n"
            "1. Нажмите на скрепку 📎 и отправьте вашу геопозицию (GPS).\n"
            "2. ЛИБО просто напишите в чат название вашего города (например: <i>Скопье</i>, <i>Битола</i>, <i>Гевгелия</i>).\n"
            "3. Затем нажмите кнопку <b>📌 Сохранить как мой дом</b> под появившимся прогнозом.\n\n"
            "🔒 <i>Ваш адрес хранится строго конфиденциально и не виден другим.</i>"
        )
        call_tg("sendMessage", {"chat_id": chat_id, "text": prompt, "parse_mode": "HTML"})
        return

    if data.startswith("save_home:"):
        # Format: save_home:lat:lon:name
        parts = data.split(":", 3)
        if len(parts) >= 4:
            lat = float(parts[1])
            lon = float(parts[2])
            name = parts[3]
            set_user_home(chat_id, name, lat, lon)
            ack = (
                f"✅ <b>'{name}' saved as your personal Home Location!</b>\n\n"
                "Tap <b>🏠 My Home</b> in the menu anytime to check it."
            ) if lang == "en" else (
                f"✅ <b>'{name}' успешно сохранён как ваш домашний адрес!</b>\n\n"
                "Теперь кнопка <b>🏠 Мой дом</b> всегда покажет погоду дома в 1 клик."
            )
            call_tg("sendMessage", {"chat_id": chat_id, "text": ack, "parse_mode": "HTML"})
            send_main_menu(chat_id, lang)
        return

    if data.startswith("city:"):
        city_key = data.split(":")[1]
        cities = {
            "skopje": (41.9981, 21.4254, "Skopje Valley" if lang=="en" else "Скопье (Котловина)"),
            "ohrid": (41.1128, 20.8019, "Ohrid Lakefront" if lang=="en" else "Охрид (Озеро)"),
            "bitola": (41.0319, 21.3347, "Bitola (Pelagonia)" if lang=="en" else "Битола (Пелагония)"),
            "strumica": (41.4375, 22.6433, "Strumica Valley" if lang=="en" else "Струмица"),
            "kavadarci": (41.4331, 22.0119, "Kavadarci (Tikves)" if lang=="en" else "Кавадарци (Тиквеш)"),
            "mavrovo": (41.6547, 20.7336, "Mavrovo National Park" if lang=="en" else "Маврово (Нацпарк)")
        }
        if city_key in cities:
            lat, lon, cname = cities[city_key]
            rep = get_weather_report(lat, lon, cname, lang)
            call_tg("sendMessage", {"chat_id": chat_id, "text": rep, "parse_mode": "HTML"})
        return

def handle_message(msg):
    chat_id = msg.get("chat", {}).get("id")
    if not chat_id:
        return

    lang = get_user_lang(chat_id)

    # GPS Location message
    if "location" in msg:
        loc = msg["location"]
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        loc_name = "Your GPS Point" if lang=="en" else "Ваша геопозиция"
        rep = get_weather_report(lat, lon, loc_name, lang)
        save_btn_txt = "📌 Save as My Home" if lang=="en" else "📌 Сохранить как мой дом"
        reply_markup = {
            "inline_keyboard": [
                [{"text": save_btn_txt, "callback_data": f"save_home:{lat:.4f}:{lon:.4f}:{loc_name}"}]
            ]
        }
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": rep,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        })
        return

    text = msg.get("text", "").strip()

    # /start handler
    if text.startswith("/start"):
        send_language_prompt(chat_id)
        return

    if text in ["/help", "📖 User Guide", "📖 Инструкция"]:
        send_user_guide(chat_id, lang)
        return

    if text in ["⚙️ Settings", "⚙️ Настройки", "/settings", "/lang"]:
        send_settings_menu(chat_id, lang)
        return

    if text in ["/cities", "🏙 Popular Cities", "🏙 Города Македонии"]:
        send_popular_cities(chat_id, lang)
        return

    if text in ["/app", "🌦 Open Meteo App", "🌦 Открыть метеостанцию"]:
        btn_text = "Launch Web App" if lang=="en" else "Запустить приложение"
        call_tg("sendMessage", {
            "chat_id": chat_id,
            "text": "👇 Click below to launch the full-screen interactive station:" if lang=="en" else "👇 Нажмите кнопку ниже, чтобы открыть интерактивное приложение:",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": f"🌦 {btn_text}", "web_app": {"url": WEB_APP_URL}}]
                ]
            }
        })
        return

    # Check for Home button (either "🏠 My Home" / "🏠 Мой дом" or "🏠 <City>")
    home = get_user_home(chat_id)
    is_home_press = False
    if home and (text in [f"🏠 {home['name']}", "🏠 My Home", "🏠 Мой дом"]):
        is_home_press = True
    elif text in ["🏠 Set My Home", "🏠 Задать мой дом", "🏠 My Home", "🏠 Мой дом"]:
        is_home_press = True

    if is_home_press:
        if home:
            rep = get_weather_report(home["lat"], home["lon"], f"🏠 {home['name']}", lang)
            change_txt = "✏️ Change Home Address" if lang=="en" else "✏️ Изменить домашний адрес"
            call_tg("sendMessage", {
                "chat_id": chat_id,
                "text": rep,
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": change_txt, "callback_data": "prompt_set_home"}]
                    ]
                }
            })
        else:
            prompt = (
                "🏠 <b>You haven't set your Home Address yet.</b>\n\n"
                "• Tap <b>📍 Send Location (GPS)</b> below.\n"
                "• OR simply type the name of your city/town in chat (e.g. <i>Bitola</i> or <i>Gevgelija</i>).\n\n"
                "🔒 <i>Your location is strictly confidential and never shared with others.</i>"
            ) if lang == "en" else (
                "🏠 <b>У вас пока не сохранён домашний адрес.</b>\n\n"
                "• Нажмите <b>📍 Моя геопозиция (GPS)</b> внизу.\n"
                "• ЛИБО просто напишите в чат название вашего города (например: <i>Битола</i>, <i>Гевгелия</i>, <i>Скопье</i>).\n\n"
                "🔒 <i>Ваш адрес строго конфиденциален и не виден другим пользователям.</i>"
            )
            call_tg("sendMessage", {"chat_id": chat_id, "text": prompt, "parse_mode": "HTML"})
        return

    if text in ["/storm", "⚡️ Grid Safety", "⚡️ Проверка сети"]:
        # If user has home, check their home. Otherwise fallback to Gevgelija baseline (or ask)
        if home:
            diag = get_grid_safety_diagnostic(home["lat"], home["lon"], home["name"], lang)
        else:
            diag = get_grid_safety_diagnostic(41.1465, 22.5042, "Balkan Grid Station (Gevgelija)", lang)
        call_tg("sendMessage", {"chat_id": chat_id, "text": diag, "parse_mode": "HTML"})
        return

    # Geocoding search: Stage 1 (Open-Meteo for cities & towns)
    encoded = urllib.parse.quote(text)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&format=json"
    try:
        req = urllib.request.Request(geo_url, headers={'User-Agent': 'BalkanMeteoBot/2.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            geo_data = json.loads(resp.read().decode('utf-8'))
            results = geo_data.get('results', [])
            if results:
                r = results[0]
                city_name = f"{r['name']}, {r.get('country','')}"
                rep = get_weather_report(r['latitude'], r['longitude'], city_name, lang)
                save_btn_txt = "📌 Save as My Home" if lang=="en" else "📌 Сохранить как мой дом"
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": save_btn_txt, "callback_data": f"save_home:{r['latitude']:.4f}:{r['longitude']:.4f}:{r['name']}"}]
                    ]
                }
                call_tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": rep,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                })
                return
    except Exception:
        pass

    # Geocoding search: Stage 2 (OpenStreetMap Nominatim for exact streets, boulevards & addresses)
    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&accept-language=ru,mk,en"
        nom_req = urllib.request.Request(nom_url, headers={'User-Agent': 'MacedoniaMeteoBot/2.0 (contact@meteo.internal)'})
        with urllib.request.urlopen(nom_req, timeout=8) as resp:
            nom_data = json.loads(resp.read().decode('utf-8'))
            if nom_data:
                r = nom_data[0]
                lat = float(r['lat'])
                lon = float(r['lon'])
                display_parts = r.get('display_name', '').split(',')
                short_name = ', '.join([p.strip() for p in display_parts[:3]]) if len(display_parts) >= 3 else r.get('display_name', '')
                rep = get_weather_report(lat, lon, short_name, lang)
                save_btn_txt = "📌 Save as My Home" if lang=="en" else "📌 Сохранить как мой дом"
                home_save_name = display_parts[0].strip() if display_parts else "Home"
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": save_btn_txt, "callback_data": f"save_home:{lat:.4f}:{lon:.4f}:{home_save_name}"}]
                    ]
                }
                call_tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": rep,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                })
                return
    except Exception as e:
        print(f"Nominatim error: {e}", flush=True)

    fallback_msg = "Command not recognized. Tap /app or choose from the menu." if lang=="en" else "Команда не распознана. Нажмите /app или выберите кнопку в меню."
    call_tg("sendMessage", {"chat_id": chat_id, "text": fallback_msg})

def run_loop():
    print("Bot polling started with Privacy Architecture for @macedonia_meteo_bot...", flush=True)
    offset = 0
    while True:
        try:
            res = call_tg("getUpdates", {"offset": offset, "timeout": 20})
            if res and res.get("ok"):
                for upd in res.get("result", []):
                    offset = upd["update_id"] + 1
                    if "callback_query" in upd:
                        handle_callback_query(upd["callback_query"])
                    elif "message" in upd:
                        handle_message(upd["message"])
            time.sleep(0.5)
        except Exception as e:
            print(f"Polling loop exception: {e}", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    run_loop()
