import urllib.request
import json
import os
import datetime

GEVGELIJA_LAT = 41.14027
GEVGELIJA_LON = 22.50207
EVZONOI_LAT = 41.106
EVZONOI_LON = 22.554

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'GevgelijaWeatherBot/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

# 1. Fetch current data
gev_url = (f"https://api.open-meteo.com/v1/forecast?latitude={GEVGELIJA_LAT}&longitude={GEVGELIJA_LON}"
           "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,surface_pressure,weather_code"
           "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max"
           "&timezone=auto&wind_speed_unit=ms")
gev_data = fetch_json(gev_url)

evz_url = (f"https://api.open-meteo.com/v1/forecast?latitude={EVZONOI_LAT}&longitude={EVZONOI_LON}"
           "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
           "&timezone=auto&wind_speed_unit=ms")
evz_data = fetch_json(evz_url)

aq_url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={GEVGELIJA_LAT}&longitude={GEVGELIJA_LON}"
          "&current=european_aqi,pm2_5,pm10&timezone=auto")
aq_data = fetch_json(aq_url)

cur_gev = gev_data['current']
cur_evz = evz_data['current']
cur_aq = aq_data['current']

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

t_gev = cur_gev['temperature_2m']
app_gev = cur_gev['apparent_temperature']
hum_gev = cur_gev['relative_humidity_2m']
wind_gev = cur_gev['wind_speed_10m']
gust_gev = cur_gev['wind_gusts_10m']
press_hpa = cur_gev['surface_pressure']
press_mmhg = round(press_hpa * 0.750062)
w_code = cur_gev['weather_code']

t_evz = cur_evz['temperature_2m']
hum_evz = cur_evz['relative_humidity_2m']
wind_evz = cur_evz['wind_speed_10m']
press_evz = round(cur_evz['surface_pressure'] * 0.750062)

aqi = cur_aq['european_aqi']
pm25 = cur_aq['pm2_5']
pm10 = cur_aq['pm10']

# 2. Check history for 3h trends
press_trend = "стабильное"
prev_press = press_mmhg
if os.path.exists("history.csv"):
    try:
        with open("history.csv", "r", encoding="utf-8") as f:
            lines = [line.strip().split(",") for line in f if line.strip()]
        if len(lines) > 2:
            # Check 3 hours ago or last available
            idx = max(1, len(lines) - 3)
            prev_press = float(lines[idx][4])
            diff = press_mmhg - prev_press
            if diff >= 1.5:
                press_trend = "растёт"
            elif diff <= -1.5:
                press_trend = "падает"
    except Exception as e:
        print("History read warning:", e)

# Weather code descriptions
WMO_DESC = {
    0: "ясно", 1: "в основном ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь", 51: "лёгкая морось", 53: "морось", 55: "густая морось",
    61: "небольшой дождь", 63: "умеренный дождь", 65: "сильный дождь",
    80: "ливневый дождь", 95: "гроза"
}
desc = WMO_DESC.get(w_code, "облачно")

# Spoken summary for Marina
spoken_text = f"В Гевгелии сейчас плюс {round(t_gev)}, ощущается как плюс {round(app_gev)}, {desc}. Давление {press_mmhg} миллиметров ртутного столба, {press_trend}. Ветер {round(wind_gev)} метра в секунду, воздух чистый."

# 3. Append to history.csv
row = f"{now_str},{t_gev},{app_gev},{hum_gev},{press_mmhg},{wind_gev},{gust_gev},{w_code},{t_evz},{hum_evz},{press_evz},{wind_evz},{aqi},{pm25},{pm10}\n"
header = "timestamp,gev_temp,gev_apparent,gev_humidity,gev_pressure,gev_wind,gev_gusts,gev_code,evz_temp,evz_humidity,evz_pressure,evz_wind,aqi,pm25,pm10\n"

if not os.path.exists("history.csv") or os.path.getsize("history.csv") == 0:
    with open("history.csv", "w", encoding="utf-8") as f:
        f.write(header)

with open("history.csv", "a", encoding="utf-8") as f:
    f.write(row)

# 4. Save latest.json
latest = {
    "timestamp": now_str,
    "spoken_text": spoken_text,
    "gevgelija": {
        "temperature": t_gev,
        "apparent_temperature": app_gev,
        "humidity": hum_gev,
        "pressure_mmhg": press_mmhg,
        "pressure_trend": press_trend,
        "wind_speed": wind_gev,
        "wind_gusts": gust_gev,
        "weather_code": w_code,
        "description": desc
    },
    "evzonoi_greece": {
        "temperature": t_evz,
        "humidity": hum_evz,
        "pressure_mmhg": press_evz,
        "wind_speed": wind_evz
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

# 5. Update README.md
readme = f"""# 🌤️ Метеостанция Гевгелия (Северная Македония)

Автоматический микроклиматический сборщик метеоданных для Гевгелии (станция WMO 13597 / 41.14°N 22.50°E) и греческой границы (Эвзони).

### 📍 Текущие показатели на {now_str}:
* **Температура в Гевгелии:** **{t_gev}°C** (ощущается как {app_gev}°C)
* **Погода:** {desc.capitalize()}
* **Атмосферное давление:** {press_mmhg} мм рт. ст. (тренд: **{press_trend}**)
* **Ветер:** {wind_gev} м/с (порывы до {gust_gev} м/с)
* **Качество воздуха (PM2.5):** {pm25} µg/m³ (Европейский индекс AQI: {aqi} — чисто)
* **Южный рубеж (Эвзони, Греция):** {t_evz}°C, влажность {hum_evz}%, ветер {wind_evz} м/с

---
Данные обновляются каждый час в облаке Microsoft GitHub Actions.
"""
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("Collection completed successfully!")
