"""
Trans-Balkan Physics-Informed ML Deep Trainer (160 Stations)
Trains multi-station physics-informed stacking ensemble over 12 years of climate history (2014-2025).
Evaluates on unseen 2025 blind exam test split across 5 primary Balkan hubs:
- MK_GEVGELIJA (Creator Home Hub)
- MK_SKOPJE (Capital Basin)
- RS_BG_VRACAR (Pannonia Hub)
- RS_NIS (Morava Corridor)
- GR_THESSALONIKI_AIR (Aegean Maritime Interface)
"""

import sys
import os
import json
import time
import math
import urllib.request
import urllib.parse
from datetime import datetime

def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)

def fetch_station_archive(stations, start_date="2014-01-01", end_date="2025-12-31"):
    log(f"Starting 12-year climate archive ingestion for {len(stations)} stations ({start_date} to {end_date})...")
    batch_size = 20
    all_data = {}
    
    for i in range(0, len(stations), batch_size):
        batch = stations[i:i + batch_size]
        lats = ",".join(str(s["lat"]) for s in batch)
        lons = ",".join(str(s["lon"]) for s in batch)
        
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lats}&longitude={lons}&"
            f"start_date={start_date}&end_date={end_date}&"
            f"daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            f"precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,"
            f"wind_direction_10m_dominant&"
            f"timezone=UTC"
        )
        
        req = urllib.request.Request(url, headers={"User-Agent": "BalkanMeteoDeepTrainer/2.0"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    raw = json.loads(resp.read().decode())
                    if isinstance(raw, list):
                        for s_meta, s_data in zip(batch, raw):
                            all_data[s_meta["id"]] = s_data.get("daily", {})
                    else:
                        all_data[batch[0]["id"]] = raw.get("daily", {})
                log(f"  Batch {i // batch_size + 1}/{(len(stations) + batch_size - 1) // batch_size} ingested ({len(batch)} stations)")
                break
            except Exception as e:
                log(f"  Warning on batch {i}: {e}. Retrying ({attempt + 1}/4)...")
                time.sleep(3)
        time.sleep(1.0) # respectful pacing to archive API
        
    log(f"Climate ingestion complete: {len(all_data)} stations stored.")
    return all_data

def compute_physics_features(station_data, stations_dict):
    log("Computing 15 Physics-Informed atmospheric vectors & teleconnection gradients...")
    records = []
    
    # Key anchor stations for teleconnections
    skopje_id = "MK_SKOPJE"
    gevgelija_id = "MK_GEVGELIJA"
    belgrade_id = "RS_BG_VRACAR"
    nis_id = "RS_NIS"
    thessaloniki_id = "GR_THESSALONIKI_AIR"
    kopaonik_id = "RS_KOPAONIK"
    popova_sapka_id = "MK_POPOVA_SAPKA"
    
    # Base timeline from Gevgelija
    gev_times = station_data.get(gevgelija_id, {}).get("time", [])
    if not gev_times:
        for s_id, s_d in station_data.items():
            if "time" in s_d:
                gev_times = s_d["time"]
                break
                
    num_days = len(gev_times)
    log(f"Aligning {num_days} daily steps across 160 stations (~12 years)...")
    
    for idx in range(num_days):
        t_str = gev_times[idx]
        dt = datetime.strptime(t_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday
        
        # 1. Solar Zenith Angle / Orbital insolation harmonic
        sin_day = math.sin(2 * math.pi * day_of_year / 365.25)
        cos_day = math.cos(2 * math.pi * day_of_year / 365.25)
        
        # 2. Inversion Index: Kopaonik mountain (1710m) vs Nis valley (202m) lapse rate (C/km)
        t_kop = station_data.get(kopaonik_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        t_nis = station_data.get(nis_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        lapse_kop_nis = ((t_kop - t_nis) / 1.508) if (t_kop is not None and t_nis is not None) else 0.0
        
        # 3. Inversion Index: Popova Shapka (1780m) vs Skopje (240m) lapse rate (C/km)
        t_pop = station_data.get(popova_sapka_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        t_skp = station_data.get(skopje_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        lapse_pop_skp = ((t_pop - t_skp) / 1.540) if (t_pop is not None and t_skp is not None) else 0.0
        
        # 4. Teleconnection Thermal Gradient: Belgrade vs Thessaloniki (Continental vs Mediterranean)
        t_bg = station_data.get(belgrade_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        t_th = station_data.get(thessaloniki_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        teleconnection_bg_th = (t_th - t_bg) if (t_th is not None and t_bg is not None) else 0.0
        
        # 5. Vardar Corridor Foehn / Advection gradient: Skopje vs Gevgelija
        t_gev = station_data.get(gevgelija_id, {}).get("temperature_2m_mean", [None]*num_days)[idx]
        vardar_gradient = (t_gev - t_skp) if (t_gev is not None and t_skp is not None) else 0.0
        
        step_entry = {
            "date": t_str,
            "sin_day": sin_day,
            "cos_day": cos_day,
            "lapse_kop_nis": lapse_kop_nis,
            "lapse_pop_skp": lapse_pop_skp,
            "teleconnection_bg_th": teleconnection_bg_th,
            "vardar_gradient": vardar_gradient
        }
        
        # Ingest meteorological vectors for all stations
        for s_id, d_dict in station_data.items():
            t_mean = d_dict.get("temperature_2m_mean", [None]*num_days)[idx]
            w_max = d_dict.get("wind_speed_10m_max", [None]*num_days)[idx]
            w_dir = d_dict.get("wind_direction_10m_dominant", [None]*num_days)[idx]
            precip = d_dict.get("precipitation_sum", [None]*num_days)[idx]
            
            if t_mean is not None:
                step_entry[f"{s_id}_temp"] = t_mean
            if w_max is not None:
                step_entry[f"{s_id}_wind"] = w_max
            if precip is not None:
                step_entry[f"{s_id}_precip"] = precip
            if w_dir is not None and w_max is not None:
                rad = math.radians(w_dir)
                step_entry[f"{s_id}_u"] = -w_max * math.sin(rad)
                step_entry[f"{s_id}_v"] = -w_max * math.cos(rad)
                
        records.append(step_entry)
        
    log(f"Physics feature matrix built: {len(records)} time steps.")
    return records

def train_and_evaluate(records, target_station="MK_GEVGELIJA"):
    log(f"Initiating Stacking Ensemble training for target: {target_station}...")
    
    # Split: Train on 2014-2024 (11 years), Test on 2025 (Unseen blind exam)
    train_records = [r for r in records if r["date"] < "2025-01-01"]
    test_records = [r for r in records if r["date"] >= "2025-01-01"]
    
    log(f"  Training samples (2014-2024): {len(train_records)} days")
    log(f"  Testing samples  (2025-2026): {len(test_records)} days (Blind examination)")
    
    target_key = f"{target_station}_temp"
    feature_keys = [k for k in train_records[0].keys() if k not in ("date", target_key)]
    
    X_train = [[r.get(k, 0.0) or 0.0 for k in feature_keys] for r in train_records]
    y_train = [r.get(target_key, 15.0) or 15.0 for r in train_records]
    
    X_test = [[r.get(k, 0.0) or 0.0 for k in feature_keys] for r in test_records]
    y_test = [r.get(target_key, 15.0) or 15.0 for r in test_records]
    
    from sklearn.linear_model import Ridge
    import lightgbm as lgb
    
    # Model 1: Physical Linear Regularizer
    log("  Fitting Model 1: Ridge Physical Regularizer (L2 alpha=15.0)...")
    ridge = Ridge(alpha=15.0)
    ridge.fit(X_train, y_train)
    pred_ridge = ridge.predict(X_test)
    
    # Model 2: Ultra-Deep LightGBM Regressor
    log("  Fitting Model 2: LightGBM Gradient Booster (800 trees, depth 7, lr 0.02)...")
    lgbm = lgb.LGBMRegressor(
        n_estimators=800,
        learning_rate=0.02,
        max_depth=7,
        num_leaves=63,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        verbose=-1
    )
    lgbm.fit(X_train, y_train)
    pred_lgbm = lgbm.predict(X_test)
    
    # Ensemble Stacking Blend (80% Non-Linear Trees + 20% Physical Linear Baseline)
    pred_ensemble = [0.80 * l + 0.20 * r for l, r in zip(pred_lgbm, pred_ridge)]
    
    # Model 3: Dual-Head Meta-Critic (Residual Error & Uncertainty Estimator)
    log("  Fitting Model 3: Meta-Critic (Predicts prediction residual sigma)...")
    train_pred_lgbm = lgbm.predict(X_train)
    residuals_train = [abs(yt - yp) for yt, yp in zip(y_train, train_pred_lgbm)]
    critic = lgb.LGBMRegressor(
        n_estimators=250,
        learning_rate=0.03,
        max_depth=5,
        random_state=42,
        verbose=-1
    )
    critic.fit(X_train, residuals_train)
    pred_critic_error = critic.predict(X_test)
    
    # Metrics
    errors = [abs(yt - yp) for yt, yp in zip(y_test, pred_ensemble)]
    mae = sum(errors) / len(errors) if errors else 0.0
    rmse = math.sqrt(sum(e**2 for e in errors) / len(errors)) if errors else 0.0
    within_05c = sum(1 for e in errors if e <= 0.5) / len(errors) * 100 if errors else 0.0
    within_1c = sum(1 for e in errors if e <= 1.0) / len(errors) * 100 if errors else 0.0
    within_2c = sum(1 for e in errors if e <= 2.0) / len(errors) * 100 if errors else 0.0
    
    log(f"============================================================")
    log(f"EXAM RESULTS FOR {target_station} ON UNSEEN 2025 BLIND TEST:")
    log(f"   • Mean Absolute Error (MAE) : {mae:.3f} °C")
    log(f"   • Root Mean Square Error    : {rmse:.3f} °C")
    log(f"   • Accuracy within ±0.5 °C   : {within_05c:.1f} %")
    log(f"   • Accuracy within ±1.0 °C   : {within_1c:.1f} %")
    log(f"   • Accuracy within ±2.0 °C   : {within_2c:.1f} %")
    log(f"   • Mean Critic Predicted Err : {sum(pred_critic_error)/len(pred_critic_error):.3f} °C")
    log(f"============================================================")
    
    # Top features from Ridge
    coefs = ridge.coef_
    top_indices = sorted(range(len(coefs)), key=lambda i: abs(coefs[i]), reverse=True)[:10]
    top_features = [{feature_keys[i]: round(float(coefs[i]), 4)} for i in top_indices]
    
    return {
        "target_station": target_station,
        "mae_celsius": round(mae, 3),
        "rmse_celsius": round(rmse, 3),
        "accuracy_within_05c_percent": round(within_05c, 1),
        "accuracy_within_1c_percent": round(within_1c, 1),
        "accuracy_within_2c_percent": round(within_2c, 1),
        "eval_days": len(y_test),
        "top_influential_features": top_features,
        "ridge_intercept": round(float(ridge.intercept_), 3)
    }

def notify_telegram(report):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    creator_chat_id = os.environ.get("CREATOR_CHAT_ID")
    if not bot_token or not creator_chat_id:
        log("Telegram notification skipped: bot_token or creator_chat_id not provided.")
        return
        
    try:
        hubs = report.get("hubs_evaluation", {})
        gev = hubs.get("MK_GEVGELIJA", {})
        skp = hubs.get("MK_SKOPJE", {})
        bg = hubs.get("RS_BG_VRACAR", {})
        nis = hubs.get("RS_NIS", {})
        th = hubs.get("GR_THESSALONIKI_AIR", {})
        
        msg = (
            "🧠 *[Balkan-Meteo AI 2.0: Deep Training Complete]*\n\n"
            "🗓️ *Период обучения:* 12 лет (2014–2025, 4380 дней)\n"
            "🛰️ *Сетка станций:* 160 станций (MK, RS, GR, AL)\n"
            f"🎯 *Средний MAE по региону:* `{report.get('overall_mean_mae', '0.00')} °C`\n\n"
            "📊 *Результаты слепого экзамена (2025 год):*\n"
            f"• 🇲🇰 *Gevgelija:* MAE `{gev.get('mae_celsius', 0)} °C` (±1°C: `{gev.get('accuracy_within_1c_percent', 0)}%`)\n"
            f"• 🇲🇰 *Skopje:* MAE `{skp.get('mae_celsius', 0)} °C` (±1°C: `{skp.get('accuracy_within_1c_percent', 0)}%`)\n"
            f"• 🇷🇸 *Belgrade:* MAE `{bg.get('mae_celsius', 0)} °C`\n"
            f"• 🇷🇸 *Nis:* MAE `{nis.get('mae_celsius', 0)} °C`\n"
            f"• 🇬🇷 *Thessaloniki:* MAE `{th.get('mae_celsius', 0)} °C`\n\n"
            "⚡ *Физические веса сохранены в репозиторий GitHub.*"
        )
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": creator_chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            log("Telegram completion notification dispatched successfully!")
    except Exception as e:
        log(f"Failed to dispatch Telegram notification: {e}")

def main():
    log("=== BALKAN DEEP TRAINER ENGINE 2.0 (12-YEAR ARCHIVE) START ===")
    
    stations_path = os.path.join(os.path.dirname(__file__), "stations_mesh_160.json")
    if not os.path.exists(stations_path):
        stations_path = "stations_mesh_160.json"
        
    with open(stations_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        stations = meta.get("stations", [])
        
    log(f"Loaded {len(stations)} stations from {stations_path}")
    
    # 1. Ingest 12-year climate archive (2014-2025)
    data = fetch_station_archive(stations, start_date="2014-01-01", end_date="2025-12-31")
    
    # 2. Physics feature engine
    features = compute_physics_features(data, {s["id"]: s for s in stations})
    
    # 3. Train & Evaluate for primary hubs
    hubs = ["MK_GEVGELIJA", "MK_SKOPJE", "RS_BG_VRACAR", "RS_NIS", "GR_THESSALONIKI_AIR"]
    reports = {}
    
    for hub in hubs:
        reports[hub] = train_and_evaluate(features, target_station=hub)
        
    # 4. Generate summary accuracy protocol
    summary_report = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "mesh_stations_count": len(stations),
        "history_window": "2014-01-01 to 2025-12-31 (12 years)",
        "eval_period": "2025-01-01 to 2025-12-31",
        "hubs_evaluation": reports,
        "overall_mean_mae": round(sum(r["mae_celsius"] for r in reports.values()) / len(reports), 3)
    }
    
    with open("accuracy_report.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
        
    # Also save portable model weights
    portable_weights = {
        "timestamp_utc": summary_report["timestamp_utc"],
        "hubs": {
            hub: {
                "intercept": reports[hub]["ridge_intercept"],
                "top_features": reports[hub]["top_influential_features"],
                "mae": reports[hub]["mae_celsius"]
            } for hub in hubs
        }
    }
    with open("balkan_weights.json", "w", encoding="utf-8") as f:
        json.dump(portable_weights, f, indent=2)
        
    log("Accuracy report and weights saved.")
    
    # 5. Dispatch Telegram completion notification
    notify_telegram(summary_report)
    
    log("=== BALKAN DEEP TRAINER ENGINE 2.0 COMPLETE ===")

if __name__ == "__main__":
    main()
