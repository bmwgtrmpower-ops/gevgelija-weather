"""
Balkan Regional Telemetry Ingestion Pipeline
Automated multi-station weather aggregator across:
- North Macedonia (Vardar Valley, Ohrid, Pelagonia, Skopje, Ski resorts)
- Serbia (Belgrade, Novi Sad, Niš, Kragujevac, Kopaonik, Zlatibor, Vršac)
- Greece (Thessaloniki, Aegean border)
- Albania (Tirana, Korçë)
"""

import urllib.request
import json
import os
import datetime
import sys

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STATIONS = {
    # --- North Macedonia ---
    'home':  {'name': 'Гевгелия (Южный регион)', 'region': 'Гевгелия', 'lat': 41.1465, 'lon': 22.5042},
    'koz':   {'name': 'Кожуф (Горный пик, 1370м)', 'region': 'Кожуф', 'lat': 41.2100, 'lon': 22.2800},
    'bog':   {'name': 'Богданци (Ветропарк)', 'region': 'Богданци', 'lat': 41.2000, 'lon': 22.5800},
    'doj':   {'name': 'Дойранское озеро (Стар Дојран)', 'region': 'Дойран', 'lat': 41.1800, 'lon': 22.7200},
    'val':   {'name': 'Валандово (Каньон)', 'region': 'Валандово', 'lat': 41.3100, 'lon': 22.5600},
    'dmk':   {'name': 'Демир Капия (Железные ворота)', 'region': 'Демир Капия', 'lat': 41.4100, 'lon': 22.2500},
    'kav':   {'name': 'Кавадарци / Тиквеш', 'region': 'Тиквеш', 'lat': 41.4300, 'lon': 22.0100},
    'neg':   {'name': 'Неготино', 'region': 'Вардар', 'lat': 41.4800, 'lon': 22.0900},
    'vel':   {'name': 'Велес (Центр долины)', 'region': 'Велес', 'lat': 41.7100, 'lon': 21.7700},
    'str':   {'name': 'Струмица (Беласица)', 'region': 'Струмица', 'lat': 41.4300, 'lon': 22.6400},
    'rad':   {'name': 'Радовиш', 'region': 'Радовиш', 'lat': 41.6300, 'lon': 22.4600},
    'skp_c': {'name': 'Скопье (Центр)', 'region': 'Скопье', 'lat': 41.9900, 'lon': 21.4300},
    'skp_v': {'name': 'Скопье (Гора Водно, 1066м)', 'region': 'Скопье', 'lat': 41.9600, 'lon': 21.4000},
    'skp_a': {'name': 'Скопье (Аэропорт Петровец)', 'region': 'Скопье', 'lat': 41.9600, 'lon': 21.6200},
    'mav':   {'name': 'Маврово (Лыжный центр, 1280м)', 'region': 'Маврово', 'lat': 41.7000, 'lon': 20.7300},
    'pop':   {'name': 'Попова Шапка (Шар-Планина, 1740м)', 'region': 'Попова Шапка', 'lat': 42.0100, 'lon': 20.8800},
    'tet':   {'name': 'Тетово (Полог)', 'region': 'Тетово', 'lat': 42.0100, 'lon': 20.9700},
    'gos':   {'name': 'Гостивар', 'region': 'Гостивар', 'lat': 41.8000, 'lon': 20.9100},
    'deb':   {'name': 'Дебар (Дебарское озеро)', 'region': 'Дебар', 'lat': 41.5200, 'lon': 20.5200},
    'ohr':   {'name': 'Охрид (Охридское озеро)', 'region': 'Охрид', 'lat': 41.1100, 'lon': 20.8000},
    'stg':   {'name': 'Струга (Чёрный Дрин)', 'region': 'Струга', 'lat': 41.1700, 'lon': 20.6700},
    'gal':   {'name': 'Галичица (Перевал, 1620м)', 'region': 'Галичица', 'lat': 40.9500, 'lon': 20.8300},
    'res':   {'name': 'Ресен (Преспанское озеро)', 'region': 'Преспа', 'lat': 41.0900, 'lon': 21.0100},
    'bit':   {'name': 'Битола (Пелагония)', 'region': 'Битола', 'lat': 41.0300, 'lon': 21.3300},
    'pel':   {'name': 'Пелистер (Пик Баба, 2404м)', 'region': 'Пелистер', 'lat': 41.0000, 'lon': 21.1800},
    'pri':   {'name': 'Прилеп', 'region': 'Прилеп', 'lat': 41.3400, 'lon': 21.5500},
    'kru':   {'name': 'Крушево (Высокогорный город, 1235м)', 'region': 'Крушево', 'lat': 41.3700, 'lon': 21.2500},
    'ber':   {'name': 'Берово (Малешевские горы)', 'region': 'Берово', 'lat': 41.7000, 'lon': 22.8500},
    'peh':   {'name': 'Пехчево', 'region': 'Пехчево', 'lat': 41.7600, 'lon': 22.8800},
    'koc':   {'name': 'Кочани (Осогово / Пониква)', 'region': 'Кочани', 'lat': 41.9100, 'lon': 22.4100},
    'sti':   {'name': 'Штип (Овче Поле)', 'region': 'Штип', 'lat': 41.7400, 'lon': 22.1900},
    'kum':   {'name': 'Куманово', 'region': 'Куманово', 'lat': 42.1300, 'lon': 21.7100},
    'krv':   {'name': 'Крива Паланка (Граница Болгарии)', 'region': 'Крива Паланка', 'lat': 42.2000, 'lon': 22.3300},

    # --- Serbia (Belgrade, Vojvodina, Nis, Mountains) ---
    'beg_c': {'name': 'Белград (Центр / Калемегдан)', 'region': 'Сербия / Белград', 'lat': 44.8176, 'lon': 20.4633},
    'beg_n': {'name': 'Нови Белград (Экспат & Бизнес хаб)', 'region': 'Сербия / Белград', 'lat': 44.8050, 'lon': 20.4130},
    'beg_a': {'name': 'Белград (Аэропорт Сурчин / Ветромер)', 'region': 'Сербия / Белград', 'lat': 44.8184, 'lon': 20.3091},
    'nsad':  {'name': 'Нови Сад (Центр / Воеводина)', 'region': 'Сербия / Нови Сад', 'lat': 45.2671, 'lon': 19.8335},
    'sub':   {'name': 'Суботица (Северная Воеводина)', 'region': 'Сербия / Суботица', 'lat': 46.1005, 'lon': 19.6651},
    'vrs':   {'name': 'Вршац (Эпицентр Кошавы)', 'region': 'Сербия / Банат', 'lat': 45.1167, 'lon': 21.3000},
    'kgv':   {'name': 'Крагуевац (Шумадия)', 'region': 'Сербия / Шумадия', 'lat': 44.0128, 'lon': 20.9114},
    'nis':   {'name': 'Ниш (Южная Сербия)', 'region': 'Сербия / Ниш', 'lat': 43.3209, 'lon': 21.8958},
    'kop':   {'name': 'Копаоник (Горнолыжный курорт, 1770м)', 'region': 'Сербия / Копаоник', 'lat': 43.2858, 'lon': 20.8108},
    'zla':   {'name': 'Златибор (Горный курорт, 1010м)', 'region': 'Сербия / Златибор', 'lat': 43.7258, 'lon': 19.7033},
    'tar':   {'name': 'Тара (Национальный парк)', 'region': 'Сербия / Тара', 'lat': 43.8500, 'lon': 19.4500},
    'stp':   {'name': 'Стара Планина (Бабин Зуб, 1550м)', 'region': 'Сербия / Восток', 'lat': 43.3750, 'lon': 22.6167},

    # --- Greece & Albania Border Network ---
    'evz':   {'name': 'Эвзони (КПП границы Греции, 45м)', 'region': 'Греция', 'lat': 41.1100, 'lon': 22.5500},
    'the':   {'name': 'Салоники (Эгейское море, 5м)', 'region': 'Греция', 'lat': 40.6400, 'lon': 22.9400},
    'tir':   {'name': 'Тирана / Адриатика (110м)', 'region': 'Албания', 'lat': 41.3300, 'lon': 19.8200},
    'kor':   {'name': 'Корча (Юго-восток Албании, 850м)', 'region': 'Албания', 'lat': 40.6100, 'lon': 20.7800}
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BalkanTelemetryPipeline/2.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print(f"Collecting data for {len(STATIONS)} stations across Macedonia, Serbia, Greece, and Albania...", flush=True)
    lats = ','.join(str(s['lat']) for s in STATIONS.values())
    lons = ','.join(str(s['lon']) for s in STATIONS.values())

    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}"
           "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure,weather_code"
           "&daily=precipitation_probability_max,precipitation_sum,wind_gusts_10m_max&forecast_days=2&timezone=auto&wind_speed_unit=ms")
    batch_data = fetch_json(url)

    # Air Quality for Home & Belgrade
    try:
        aq_url = ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=41.1465&longitude=22.5042"
                  "&current=european_aqi,pm2_5,pm10&timezone=auto")
        aq_data = fetch_json(aq_url)
        aq_cur = aq_data.get('current', {})
        aqi = aq_cur.get('european_aqi', 0)
        pm25 = aq_cur.get('pm2_5', 0)
        pm10 = aq_cur.get('pm10', 0)
    except Exception:
        aqi, pm25, pm10 = 0, 0, 0

    res_dict = {}
    for i, key in enumerate(STATIONS.keys()):
        item = batch_data[i] if isinstance(batch_data, list) else batch_data
        c = item['current']
        elev = item.get('elevation', 0)
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

    home = res_dict.get('home', {})
    beg = res_dict.get('beg_c', {})

    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    final_output = {
        "timestamp": now_utc,
        "stations_count": len(res_dict),
        "countries_covered": ["MK", "RS", "GR", "AL"],
        "home_station": home,
        "belgrade_station": beg,
        "air_quality": {
            "european_aqi": aqi,
            "pm2_5": pm25,
            "pm10": pm10
        },
        "stations": res_dict
    }

    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated latest.json with {len(res_dict)} stations across 4 countries!", flush=True)

if __name__ == "__main__":
    main()
