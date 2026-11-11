import urllib.request
import json
import os
import datetime

# 5 Cluster Stations across Gevgelija Basin & Greek Border
STATIONS = {
    'gev': {'name': 'Гевгелия (Центр)', 'lat': 41.14027, 'lon': 22.50207, 'elev': 63},
    'koz': {'name': 'Кожуф (Западные горы)', 'lat': 41.21000, 'lon': 22.28000, 'elev': 1369},
    'val': {'name': 'Валандово (Северный каньон)', 'lat': 41.31000, 'lon': 22.56000, 'elev': 91},
    'bog': {'name': 'Богданци (Восточные холмы)', 'lat': 41.20000, 'lon': 22.58000, 'elev': 83},
    'evz': {'name': 'Эвзони / Поликастро (Греция, Юг)', 'lat': 41.00000, 'lon': 22.57000, 'elev': 43}
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'GevgelijaBasinCollector/2.0'})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode('utf-8'))

lats = ','.join(str(s['lat']) for s in STATIONS.values())
lons = ','.join(str(s['lon']) for s in STATIONS.values())

# 1. Fetch Cluster Weather
weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}"
               "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure,weather_code"
               "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max"
               "&timezone=auto&wind_speed_unit=ms")
cluster_data = fetch_json(weather_url)

# 2. Fetch Air Quality
aq_url = ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=41.14027&longitude=22.50207"
          "&current=european_aqi,pm2_5,pm10&timezone=auto")
aq_data = fetch_json(aq_url)

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

# Parse 5 stations
st_res = {}
keys = list(STATIONS.keys())
for i, k in enumerate(keys):
    c = cluster_data[i]['current']
    st_res[k] = {
        'name': STATIONS[k]['name'],
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

# Wind direction helper
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

gev = st_res['gev']
evz = st_res['evz']
val = st_res['val']
koz = st_res['koz']
bog = st_res['bog']

cur_aq = aq_data['current']
aqi = cur_aq['european_aqi']
pm25 = cur_aq['pm2_5']
pm10 = cur_aq['pm10']

# 3. Aerodynamic & Air Mass Analysis
gev_wind_name = wind_dir_text(gev['wind_dir'])
press_grad = evz['pressure_hpa'] - val['pressure_hpa']

if press_grad >= 1.5:
    air_mass = "Поток тёплого средиземноморского воздуха из Греции поднимается по руслу Вардара."
elif press_grad <= -1.5:
    air_mass = "С севера по ущелью Вардара заходит сухой прохладный ветер Вардарец."
else:
    air_mass = "Барометрическое поле стабильное, спокойное перемещение воздушных масс."

# Inversion check
temp_diff_mount = gev['temp'] - koz['temp']
if temp_diff_mount < 3.5:
    inversion_note = "Обнаружена слабая температурная инверсия в низине."
else:
    inversion_note = "Атмосферный градиент в норме, воздух чистый."

# Weather code descriptions
WMO_DESC = {
    0: "ясно", 1: "в основном ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь", 51: "лёгкая морось", 53: "морось", 55: "густая морось",
    61: "небольшой дождь", 63: "умеренный дождь", 65: "сильный дождь",
    80: "ливневый дождь", 95: "гроза"
}
desc = WMO_DESC.get(gev['weather_code'], "облачно")

# Spoken summary for Marina
spoken_text = (f"В Гевгелии сейчас плюс {round(gev['temp'])}, ощущается как плюс {round(gev['app_temp'])}, {desc}. "
               f"Ветер {gev_wind_name}, {round(gev['wind_speed'])} метра в секунду. "
               f"Давление {gev['pressure_mmhg']} миллиметров ртутного столба. "
               f"{air_mass}")

# 4. Save history.csv (Cluster Row)
row = (f"{now_str},{gev['temp']},{gev['app_temp']},{gev['humidity']},{gev['pressure_mmhg']},{gev['wind_speed']},{gev['wind_dir']},{gev['weather_code']},"
       f"{koz['temp']},{koz['pressure_mmhg']},{koz['wind_speed']},"
       f"{val['temp']},{val['pressure_mmhg']},{val['wind_speed']},"
       f"{bog['temp']},{bog['pressure_mmhg']},{bog['wind_speed']},"
       f"{evz['temp']},{evz['pressure_mmhg']},{evz['wind_speed']},{evz['wind_dir']},"
       f"{aqi},{pm25},{pm10}\n")

header = ("timestamp,gev_temp,gev_app,gev_hum,gev_press,gev_wind_spd,gev_wind_dir,gev_code,"
          "koz_temp,koz_press,koz_wind_spd,"
          "val_temp,val_press,val_wind_spd,"
          "bog_temp,bog_press,bog_wind_spd,"
          "evz_temp,evz_press,evz_wind_spd,evz_wind_dir,"
          "aqi,pm25,pm10\n")

if not os.path.exists("history.csv") or os.path.getsize("history.csv") == 0:
    with open("history.csv", "w", encoding="utf-8") as f:
        f.write(header)

with open("history.csv", "a", encoding="utf-8") as f:
    f.write(row)

# 5. Save latest.json
latest = {
    "timestamp": now_str,
    "spoken_text": spoken_text,
    "cluster": {
        "gevgelija_center": gev,
        "kozuf_mountain": koz,
        "valandovo_north": val,
        "bogdanci_east": bog,
        "evzonoi_greece": evz
    },
    "aerodynamics": {
        "wind_direction_name": gev_wind_name,
        "wind_direction_degrees": gev['wind_dir'],
        "pressure_gradient_south_north_hpa": round(press_grad, 2),
        "air_mass_description": air_mass,
        "mountain_temp_drop_c": round(temp_diff_mount, 1),
        "inversion_status": inversion_note
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

# 6. Update README.md
readme = f"""# 🌤️ Метеорологический кластер: Община Гевгелия и Граница Греции

Автоматический пятиточечный 3D-полигон анализа микроклимата и динамики воздушных масс (бассейн реки Вардар).

### 📡 Сводка кластера на {now_str}:

| Станция | Высота | Температура | Давление | Ветер | Направление |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Гевгелия (Центр)** | **63 м** | **{gev['temp']}°C** | **{gev['pressure_mmhg']} мм** | **{gev['wind_speed']} м/с** | **{gev_wind_name} ({gev['wind_dir']}°)** |
| **Кожуф (Западные горы)** | 1369 м | {koz['temp']}°C | {koz['pressure_mmhg']} мм | {koz['wind_speed']} м/с | Западный щит |
| **Валандово (Северный каньон)** | 91 м | {val['temp']}°C | {val['pressure_mmhg']} мм | {val['wind_speed']} м/с | Северные ворота |
| **Богданци (Восточные холмы)** | 83 м | {bog['temp']}°C | {bog['pressure_mmhg']} мм | {bog['wind_speed']} м/с | Ветропарк |
| **Эвзони (Греция, Юг)** | 43 м | {evz['temp']}°C | {evz['pressure_mmhg']} мм | {evz['wind_speed']} м/с | Морской приток |

---

### 💨 Аэродинамика воздушных масс:
* **Направление ветра в Гевгелии:** **{gev_wind_name}** ({gev['wind_dir']}°)
* **Барический перепад Юг-Север ($\Delta P$):** {round(press_grad, 2)} гПа
* **Динамика масс:** {air_mass}
* **Вертикальный температурный градиент:** На вершине Кожуфа на {round(temp_diff_mount, 1)}°C холоднее, чем в долине. {inversion_note}
* **Качество воздуха (Детсад «Сончогледи»):** PM2.5 = {pm25} µg/m³, AQI = {aqi} (чистый)

---
*Автоматическое обновление каждый час через GitHub Actions.*
"""
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("Cluster analysis and collection successfully completed!")
