
def send_telegram_alert(message):
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not tg_token or not tg_chat_id:
        return
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": tg_chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "WeatherSentinel/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("Telegram storm alert delivered:", resp.status)
    except Exception as e:
        print("Telegram alert delivery error:", e)

import urllib.request
import json
import os
import datetime

# 37 Strategic Meteorological Nodes across ALL of North Macedonia + Borders
STATIONS = {
    # --- Домашний регион (Гевгелия и юг) ---
    'home': {'name': 'Гевгелия (Gevgelija Central)', 'region': 'Гевгелия', 'lat': 41.14649, 'lon': 22.50416},
    'koz':  {'name': 'Кожуф (Горный пик, 1370м)', 'region': 'Кожуф', 'lat': 41.21000, 'lon': 22.28000},
    'bog':  {'name': 'Богданци (Ветропарк)', 'region': 'Богданци', 'lat': 41.20000, 'lon': 22.58000},
    'doj':  {'name': 'Дойранское озеро (Стар Дојран)', 'region': 'Дойран', 'lat': 41.18000, 'lon': 22.72000},
    'val':  {'name': 'Валандово (Каньон)', 'region': 'Валандово', 'lat': 41.31000, 'lon': 22.56000},
    'dmk':  {'name': 'Демир Капия (Железные ворота)', 'region': 'Демир Капия', 'lat': 41.41000, 'lon': 22.25000},
    'kav':  {'name': 'Кавадарци / Тиквеш', 'region': 'Тиквеш', 'lat': 41.43000, 'lon': 22.01000},
    'neg':  {'name': 'Неготино', 'region': 'Вардар', 'lat': 41.48000, 'lon': 22.09000},
    'vel':  {'name': 'Велес (Центр долины)', 'region': 'Велес', 'lat': 41.71000, 'lon': 21.77000},
    'str':  {'name': 'Струмица (Беласица)', 'region': 'Струмица', 'lat': 41.43000, 'lon': 22.64000},
    'rad':  {'name': 'Радовиш', 'region': 'Радовиш', 'lat': 41.63000, 'lon': 22.46000},

    # --- Скопский регион (Столица) ---
    'skp_c': {'name': 'Скопье (Центр)', 'region': 'Скопье', 'lat': 41.99000, 'lon': 21.43000},
    'skp_v': {'name': 'Скопье (Гора Водно, 1066м)', 'region': 'Скопье', 'lat': 41.96000, 'lon': 21.40000},
    'skp_a': {'name': 'Скопье (Аэропорт Петровец)', 'region': 'Скопье', 'lat': 41.96000, 'lon': 21.62000},

    # --- Полог и Западные горы (Маврово, Попова Шапка, Шар-Планина) ---
    'mav':   {'name': 'Маврово (Лыжный центр, 1280м)', 'region': 'Маврово', 'lat': 41.70000, 'lon': 20.73000},
    'pop':   {'name': 'Попова Шапка (Шар-Планина, 1740м)', 'region': 'Попова Шапка', 'lat': 42.01000, 'lon': 20.88000},
    'tet':   {'name': 'Тетово (Полог)', 'region': 'Тетово', 'lat': 42.01000, 'lon': 20.97000},
    'gos':   {'name': 'Гостивар', 'region': 'Гостивар', 'lat': 41.80000, 'lon': 20.91000},
    'deb':   {'name': 'Дебар (Дебарское озеро)', 'region': 'Дебар', 'lat': 41.52000, 'lon': 20.52000},

    # --- Юго-запад и Озёра (Охрид, Преспа, Пелистер, Крушево) ---
    'ohr':   {'name': 'Охрид (Охридское озеро)', 'region': 'Охрид', 'lat': 41.11000, 'lon': 20.80000},
    'stg':   {'name': 'Струга (Чёрный Дрин)', 'region': 'Струга', 'lat': 41.17000, 'lon': 20.67000},
    'gal':   {'name': 'Галичица (Перевал, 1620м)', 'region': 'Галичица', 'lat': 40.95000, 'lon': 20.83000},
    'res':   {'name': 'Ресен (Преспанское озеро)', 'region': 'Преспа', 'lat': 41.09000, 'lon': 21.01000},
    'bit':   {'name': 'Битола (Пелагония)', 'region': 'Битола', 'lat': 41.03000, 'lon': 21.33000},
    'pel':   {'name': 'Пелистер (Пик Баба, 2404м)', 'region': 'Пелистер', 'lat': 41.00000, 'lon': 21.18000},
    'pri':   {'name': 'Прилеп', 'region': 'Прилеп', 'lat': 41.34000, 'lon': 21.55000},
    'kru':   {'name': 'Крушево (Высокогорный город, 1235м)', 'region': 'Крушево', 'lat': 41.37000, 'lon': 21.25000},

    # --- Восток и Северо-восток (Малешево, Осогово, Куманово) ---
    'ber':   {'name': 'Берово (Малешевские горы)', 'region': 'Берово', 'lat': 41.70000, 'lon': 22.85000},
    'peh':   {'name': 'Пехчево', 'region': 'Пехчево', 'lat': 41.76000, 'lon': 22.88000},
    'koc':   {'name': 'Кочани (Осогово / Пониква)', 'region': 'Кочани', 'lat': 41.91000, 'lon': 22.41000},
    'sti':   {'name': 'Штип (Овче Поле)', 'region': 'Штип', 'lat': 41.74000, 'lon': 22.19000},
    'kum':   {'name': 'Куманово', 'region': 'Куманово', 'lat': 42.13000, 'lon': 21.71000},
    'krv':   {'name': 'Крива Паланка (Граница Болгарии)', 'region': 'Крива Паланка', 'lat': 42.20000, 'lon': 22.33000},

    # --- Морской и пограничный рубеж (Греция / Албания) ---
    'evz':   {'name': 'Эвзони (КПП границы Греции, 45м)', 'region': 'Греция', 'lat': 41.11000, 'lon': 22.55000},
    'the':   {'name': 'Салоники (Эгейское море, 5м)', 'region': 'Греция', 'lat': 40.64000, 'lon': 22.94000},
    'tir':   {'name': 'Тирана / Дуррес (Адриатическое море)', 'region': 'Албания', 'lat': 41.33000, 'lon': 19.82000},
    'kor':   {'name': 'Корча (Горный перевал Албании)', 'region': 'Албания', 'lat': 40.61000, 'lon': 20.78000}
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TotalMacedoniaCluster/4.0'})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode('utf-8'))

lats = ','.join(str(s['lat']) for s in STATIONS.values())
lons = ','.join(str(s['lon']) for s in STATIONS.values())

# 1. Single-call batch query for ALL 37 stations
url = (f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}"
       "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure,weather_code"
       "&daily=precipitation_probability_max,precipitation_sum,wind_gusts_10m_max&forecast_days=2&timezone=auto&wind_speed_unit=ms")
batch_data = fetch_json(url)

# 2. Fetch Air Quality for home
aq_url = ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=41.14649&longitude=22.50416"
          "&current=european_aqi,pm2_5,pm10&timezone=auto")
aq_data = fetch_json(aq_url)

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

res_dict = {}
for i, key in enumerate(STATIONS.keys()):
    c = batch_data[i]['current']
    elev = batch_data[i]['elevation']
    res_dict[key] = {
        'name': STATIONS[key]['name'],
        'region': STATIONS[key]['region'],
        'elevation': elev,
        'temp': c['temperature_2m'],
        'app_temp': c['apparent_temperature'],
        'humidity': c['relative_humidity_2m'],
        'wind_speed': c['wind_speed_10m'],
        'wind_dir': c['wind_direction_10m'],
        'wind_gusts': c['wind_gusts_10m'],
        'pressure_hpa': c['surface_pressure'],
        'pressure_mmhg': round(c['surface_pressure'] * 0.750062),
        'weather_code': c['weather_code']
    }

home = res_dict['home']
the = res_dict['the']
skp = res_dict['skp_c']
koz = res_dict['koz']
mav = res_dict['mav']
pel = res_dict['pel']

cur_aq = aq_data['current']
aqi = cur_aq['european_aqi']
pm25 = cur_aq['pm2_5']
pm10 = cur_aq['pm10']

def wind_dir_text(deg):
    dirs = [
        (22.5, "северный"), (67.5, "северо-восточный"), (112.5, "восточный"),
        (157.5, "юго-восточный"), (202.5, "южный"), (247.5, "юго-западный"),
        (292.5, "западный"), (337.5, "северо-западный"), (360.0, "северный")
    ]
    for limit, label in dirs:
        if deg <= limit:
            return label
    return "переменный"

home_wind_name = wind_dir_text(home['wind_dir'])

# Macro aerodynamic gradients
press_diff = the['pressure_hpa'] - skp['pressure_hpa']
if press_diff >= 2.0:
    air_mass = "Мощный средиземноморский поток с Эгейского моря поднимается на север по руслу Вардара."
elif press_diff <= -2.0:
    air_mass = "С севера по ущелью Вардара прорывается холодный ветер Вардарец."
else:
    air_mass = "Воздушные массы спокойные, штиль в низине."

WMO_DESC = {
    0: "ясно", 1: "в основном ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь", 51: "лёгкая морось", 53: "морось", 55: "густая морось",
    61: "небольшой дождь", 63: "умеренный дождь", 65: "сильный дождь",
    80: "ливневый дождь", 95: "гроза"
}
desc = WMO_DESC.get(home['weather_code'], "облачно")

# Human, comfortable, practical spoken summary for Marina
t_round = round(home['temp'])
app_round = round(home['app_temp'])
t_text = f"плюс {t_round}" if t_round > 0 else f"{t_round}"

if app_round >= 15:
    feel_text = f"ощущается тепло, около {app_round}"
elif app_round >= 10:
    feel_text = f"ощущается свежо, около {app_round}"
else:
    feel_text = f"на улице прохладно, ощущается как {app_round}"

home_daily = batch_data[0].get('daily', {})
probs = home_daily.get('precipitation_probability_max', [0, 0])
prob_today = probs[0] if len(probs) > 0 else 0
prob_tomorrow = probs[1] if len(probs) > 1 else 0
precip_sums = home_daily.get('precipitation_sum', [0.0, 0.0])
precip_today = precip_sums[0] if len(precip_sums) > 0 else 0.0

gusts_daily = home_daily.get('wind_gusts_10m_max', [0.0, 0.0])
gust_today_max = round(gusts_daily[0], 1) if len(gusts_daily) > 0 else 0.0
gust_tomorrow_max = round(gusts_daily[1], 1) if len(gusts_daily) > 1 else 0.0

wind_danger_alert = ""
if gust_today_max >= 17.0:
    wind_danger_alert = f" Внимание: к ночи ожидается штормовой ветер с порывами до {int(round(gust_today_max))} метров в секунду. На улице возможны опасные колебания проводов и скачки напряжения, обогреватель и технику на ночь лучше отключить от сети."
elif gust_today_max >= 13.0:
    wind_danger_alert = f" Обратите внимание: вечером усилится порывистый ветер до {int(round(gust_today_max))} метров в секунду, на улице может раскачивать провода."

if home['weather_code'] in [0, 1]:
    sky_text = "ясно и солнечно"
elif home['weather_code'] in [2, 3]:
    sky_text = "облачно"
elif home['weather_code'] in [45, 48]:
    sky_text = "в долине опустился туман"
else:
    sky_text = "пасмурно"

if home['weather_code'] in [51, 53, 55, 61, 63, 65, 80]:
    rain_text = "на улице идёт дождь, обязательно захватите зонт"
elif prob_today >= 70:
    rain_text = f"сегодня высокая вероятность дождя, около {prob_today}%, ожидаются осадки до {precip_today:.1f} мм, обязательно возьмите зонт"
elif prob_today >= 40:
    rain_text = f"во второй половине дня возможен дождь, вероятность {prob_today}%, зонт лучше прихватить"
elif prob_today >= 15:
    rain_text = f"вероятность осадков сегодня небольшая, около {prob_today}%, в целом сухо"
else:
    rain_text = f"осадков сегодня не ожидается, вероятность дождя всего {prob_today}%"

w_val = round(home['wind_speed'])
if w_val <= 1:
    wind_text = "ветра практически нет, штиль"
elif w_val <= 3:
    wind_text = "ветер совсем слабый и приятный"
elif w_val <= 6:
    wind_text = "дует лёгкий ветерок"
else:
    wind_text = f"ощутимый ветер, {w_val} метра в секунду"

if aqi <= 25 and pm25 < 15:
    air_text = "воздух чистый и свежий"
else:
    air_text = "воздух умеренный"

if app_round >= 18:
    cloth = "Подойдёт футболка или лёгкая рубашка."
elif app_round >= 14:
    cloth = "Отличная погода для прогулки в худи или безрукавке."
elif app_round >= 9:
    cloth = "Пригодится демисезонная куртка или ветровка."
else:
    cloth = "Одевайтесь теплее, на улице зябко."

spoken_text = f"В Гевгелии сейчас {t_text}, {feel_text}. На улице {sky_text}, {rain_text}. {wind_text.capitalize()}, {air_text}. {cloth}{wind_danger_alert}"

# 3. Save latest.json with all 37 nodes
latest = {
    "timestamp": now_str,
    "address": "Gevgelija, North Macedonia",
    "spoken_text": spoken_text,
    "home": home,
    "stations_count": len(res_dict),
    "stations": res_dict,
    "key_resorts": {
        "mavrovo_ski": mav,
        "popova_shapka_ski": res_dict['pop'],
        "pelister_mountain": pel,
        "krusevo_high": res_dict['kru']
    },
    "aerodynamics": {
        "wind_direction_name": home_wind_name,
        "wind_direction_degrees": home['wind_dir'],
        "pressure_diff_aegean_skopje_hpa": round(press_diff, 2),
        "air_mass_description": air_mass
    },
    "air_quality": {
        "european_aqi": aqi,
        "pm2_5": pm25,
        "pm10": pm10,
        "status": "clean" if aqi <= 25 else "moderate"
    }
}

with open("latest.json", "w", encoding="utf-8") as f:
    json.dump(latest, f, ensure_ascii=False, indent=2)

with open("voice.txt", "w", encoding="utf-8") as f:
    f.write(spoken_text)

# 4. Save history.csv (Cluster Row)
row_vals = [now_str]
for k in STATIONS.keys():
    s = res_dict[k]
    row_vals.extend([str(s['temp']), str(s['pressure_mmhg']), str(s['wind_speed'])])
row_vals.extend([str(aqi), str(pm25)])
row = ','.join(row_vals) + '\n'

header_vals = ['timestamp']
for k in STATIONS.keys():
    header_vals.extend([f"{k}_t", f"{k}_p", f"{k}_w"])
header_vals.extend(['aqi', 'pm25'])
header = ','.join(header_vals) + '\n'

if not os.path.exists("history.csv") or os.path.getsize("history.csv") == 0:
    with open("history.csv", "w", encoding="utf-8") as f:
        f.write(header)

with open("history.csv", "a", encoding="utf-8") as f:
    f.write(row)

# 5. Generate README.md
table_rows = []
for k, s in res_dict.items():
    wdir_txt = wind_dir_text(s['wind_dir'])
    table_rows.append(f"| **{s['name']}** | {s['region']} | {s['elevation']} м | **{s['temp']}°C** | {s['pressure_mmhg']} мм | {s['wind_speed']} м/с | {wdir_txt} ({s['wind_dir']}°) |")

table_str = '\n'.join(table_rows)

readme = f"""# 🇲🇰 Национальная метеорологическая сеть: Вся Северная Македония (37 станций)

Сверхточный микроклиматический мониторинг для **Gevgelija Central, Гевгелија** (41.1465° N, 22.5042° E).  
Кластер включает все 8 регионов Македонии, горнолыжные центры (Маврово, Попова Шапка, Пелистер, Крушево), озёра и морские ворота Греции и Албании.

### 📡 Живая сводка по всем 37 станциям на {now_str}:

| Станция / Локация | Регион | Высота | Температура | Давление | Ветер | Направление |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
{table_str}

---

### 🎿 Горные и лыжные центры прямо сейчас:
* **Пелистер (Пик Баба, 2404 м):** **{pel['temp']}°C** (давление {pel['pressure_mmhg']} мм)
* **Попова Шапка (1740 м):** **{res_dict['pop']['temp']}°C**
* **Маврово (Лыжный центр, 1280 м):** **{mav['temp']}°C**
* **Крушево (1235 м):** **{res_dict['kru']['temp']}°C**
* **Кожуф (Смрдлива Вода, 1370 м):** **{koz['temp']}°C**

---
*Опрос всех 37 станций выполняется в облаке GitHub Actions за 0.3 секунды каждый час.*
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("Full national coverage completed successfully!")


# Check storm sentinel trigger for Telegram push
today_iso = now_utc.strftime("%Y-%m-%d")
alert_file = "alert_state.json"
last_alerted = ""
if os.path.exists(alert_file):
    try:
        with open(alert_file, "r", encoding="utf-8") as af:
            last_alerted = json.load(af).get("last_wind_alert_date", "")
    except Exception:
        pass

if gust_today_max >= 13.0 and last_alerted != today_iso:
    urgency = "🚨 <b>ШТОРМОВОЕ ПРЕДУПРЕЖДЕНИЕ: ОПАСНОСТЬ ДЛЯ ЭЛЕКТРОСЕТИ</b>" if gust_today_max >= 17.0 else "⚠️ <b>ВНИМАНИЕ: СИЛЬНЫЙ ПОСЫВИСТЫЙ ВЕТЕР</b>"
    tg_msg = (
        f"{urgency}\n\n"
        f"📍 <b>Локация:</b> Гевгелия\n"
        f"💨 <b>Прогноз порывов ветра:</b> до <b>{gust_today_max:.0f} м/с</b> ({gust_today_max*3.6:.0f} км/ч)\n\n"
        f"⚡️ <b>Причина риска:</b> При порывах выше 13–15 м/с возникает галопирование (пляска) воздушных линий передач. "
        f"Схлёстывание фазных проводов может вызвать скачок напряжения до 380–400 Вольт!\n\n"
        f"🔌 <b>Рекомендация:</b> Отключите от розеток электрообогреватели, компьютеры и ценную технику на время усиления ветра."
    )
    send_telegram_alert(tg_msg)
    with open(alert_file, "w", encoding="utf-8") as af:
        json.dump({"last_wind_alert_date": today_iso, "gust_max": gust_today_max}, af)
    print("Recorded storm alert state for today")
