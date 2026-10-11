#!/usr/bin/env python3
"""Refugee Radar // Autonomous Humanitarian & Refugee Route Early-Warning Radar.

Single-file, standard-library-only backend:
  * fetches zero-auth public telemetry (Open-Meteo Marine & Weather, GloFAS
    river flood, UN OCHA ReliefWeb, GDELT 2.0) for three corridors,
  * evaluates three deterministic early-warning algorithms,
  * writes live_state.json (live run + 3 illustrative synthetic scenarios +
    rolling run history, all in one payload so nothing drifts out of sync),
  * serves index.html and live_state.json strictly read-only (GET/HEAD) on
    127.0.0.1:8080, refreshing telemetry every 30 minutes in a daemon thread.

Purpose: SAR pre-positioning, medical readiness and reception planning for
humanitarian responders. It is NOT a navigation or crossing-planning product.

Usage:
  python3 aegis.py            # fetch once, then serve + auto-refresh on 127.0.0.1:8080
  python3 aegis.py --once     # one fetch + self-test, then exit
"""
import argparse
import datetime
import http.server
import json
import math
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "live_state.json")
INDEX_PATH = os.path.join(HERE, "index.html")
PREVIEW_PATH = os.path.join(HERE, "preview.html")
REFRESH_SECONDS = 1800
TIMEOUT = 10
HISTORY_MAX = 10
USER_AGENT = "refugee-radar/1.0 (read-only humanitarian early-warning dashboard)"

ENDPOINTS = {
    "central_med_marine": "https://marine-api.open-meteo.com/v1/marine?latitude=35.10&longitude=11.80&hourly=wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height&forecast_days=3&timezone=UTC",
    "central_med_weather": "https://api.open-meteo.com/v1/forecast?latitude=35.10&longitude=11.80&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,precipitation,visibility&forecast_days=3&timezone=UTC",
    "balkan_mountain": "https://api.open-meteo.com/v1/forecast?latitude=44.78&longitude=15.75&hourly=temperature_2m,apparent_temperature,precipitation,snowfall,snow_depth,freezing_level_height,wind_speed_10m&forecast_days=3&timezone=UTC",
    "balkan_flood": "https://flood-api.open-meteo.com/v1/flood?latitude=45.14&longitude=16.90&daily=river_discharge,river_discharge_mean,river_discharge_max&forecast_days=7",
    "aegean_marine": "https://marine-api.open-meteo.com/v1/marine?latitude=39.25&longitude=26.40&hourly=wave_height,wave_direction,wave_period,wind_wave_height&forecast_days=3&timezone=UTC",
    "aegean_weather": "https://api.open-meteo.com/v1/forecast?latitude=39.25&longitude=26.40&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,temperature_2m&forecast_days=3&timezone=UTC",
    "reliefweb": "https://api.reliefweb.int/v1/reports?appname=aegis-humanitarian-radar&query[value]=mediterranean+OR+refugees+OR+balkans+OR+lampedusa+OR+lesbos&limit=5&preset=latest",
    "gdelt": "https://api.gdeltproject.org/api/v2/doc/doc?query=(lampedusa%20OR%20lesbos%20OR%20bihac%20OR%20mediterranean)%20(migrants%20OR%20rescue%20OR%20coastguard%20OR%20refugees)&mode=ArtList&maxrecords=6&format=json&timespan=72h",
}

CORRIDOR_IDS = ["central_med", "balkan_land", "aegean_east"]
SCENARIO_KEYS = ["sicily_trap", "balkan_freeze", "aegean_surge"]
CORRIDOR_GEO = {
    "central_med": {
        "name": "Central Med (Tunisia → Lampedusa)", "short_name": "Central Med",
        "origin": [10.76, 34.74], "origin_name": "Sfax / Zarzis Coast",
        "midpoint": [11.80, 35.10], "midpoint_name": "Sicily Strait SAR Zone",
        "destination": [12.60, 35.50], "destination_name": "Lampedusa Reception",
    },
    "balkan_land": {
        "name": "Balkan Route (Bihać → Sava/Una)", "short_name": "Balkan Route",
        "origin": [15.87, 44.81], "origin_name": "Bihać, Bosnia",
        "midpoint": [15.75, 44.78], "midpoint_name": "Plješevica Pass (1,200 m)",
        "destination": [16.90, 45.14], "destination_name": "Sava/Una River Border",
    },
    "aegean_east": {
        "name": "Aegean (Çeşme → Lesbos)", "short_name": "Aegean",
        "origin": [26.69, 39.32], "origin_name": "Çeşme Coast",
        "midpoint": [26.40, 39.25], "midpoint_name": "Aegean Mid-Channel",
        "destination": [26.55, 39.10], "destination_name": "Lesbos Reception",
    },
}
LABELS10 = ["T+%dh" % h for h in range(0, 40, 4)]
_LOCK = threading.Lock()


# --------------------------------------------------------------------------- helpers
def log(msg):
    sys.stderr.write("[%s] %s\n" % (datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), msg))


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def r2(x):
    return round(float(x), 2)


def synth(base, amp, period, phase, n):
    return [round(base + amp * math.sin(2 * math.pi * (h + phase) / period), 2) for h in range(n)]


def pick(payload, group, key, n, fallback, missing, tag):
    """Return n cleaned floats from payload[group][key]; synthetic fallback if absent."""
    vals = None
    try:
        vals = payload[group][key]
    except (TypeError, KeyError):
        pass
    out, last = [], None
    for v in (vals or [])[:n]:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            last = float(v)
        out.append(last)
    first = next((v for v in out if v is not None), None)
    if first is None:
        if tag:
            missing.add(tag)
        return synth(fallback[0], fallback[1], fallback[2], fallback[3], n)
    out = [first if v is None else v for v in out]
    while len(out) < n:
        out.append(out[-1])
    return out


def sample(vals):
    return [r2(vals[i]) for i in range(0, 40, 4)]


def beaufort(kmh):
    return sum(1 for t in (1, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118) if kmh >= t)


def circ_mean(deg):
    s = sum(math.sin(math.radians(d)) for d in deg)
    c = sum(math.cos(math.radians(d)) for d in deg)
    return (math.degrees(math.atan2(s, c)) + 360) % 360


def risk_color(r):
    return "#F43F5E" if r >= 75 else "#FB923C" if r >= 50 else "#FBBF24" if r >= 25 else "#34D399"


def global_level(r):
    return "CRITICAL" if r >= 85 else "HIGH" if r >= 65 else "ELEVATED" if r >= 40 else "GUARDED" if r >= 20 else "LOW"


HISTORICAL_DATA = {
    "central_med": {
        "source": "UNHCR Operational Data Portal & IOM Missing Migrants (Central Mediterranean)",
        "annual_2024_arrivals": 66280,
        "annual_2025_arrivals": 71420,
        "annual_2025_fatalities": 1478,
        "monthly_trend": [
            {"month": "Okt 25", "arrivals": 6420, "fatalities": 142},
            {"month": "Nov 25", "arrivals": 4180, "fatalities": 98},
            {"month": "Dez 25", "arrivals": 2950, "fatalities": 84},
            {"month": "Jan 26", "arrivals": 2100, "fatalities": 65},
            {"month": "Feb 26", "arrivals": 2450, "fatalities": 71},
            {"month": "Mär 26", "arrivals": 3820, "fatalities": 92},
            {"month": "Apr 26", "arrivals": 5640, "fatalities": 115},
            {"month": "Mai 26", "arrivals": 7890, "fatalities": 154},
            {"month": "Jun 26", "arrivals": 9420, "fatalities": 188},
            {"month": "Jul 26", "arrivals": 11200, "fatalities": 210},
            {"month": "Aug 26", "arrivals": 12850, "fatalities": 245},
            {"month": "Sep 26", "arrivals": 8940, "fatalities": 168},
        ],
        "hotspot_name": "Hotspot Lampedusa (Contrada Imbriacola)",
        "capacity_nominal": 850,
        "capacity_max": 1400,
        "current_occupancy": 680,
    },
    "aegean_east": {
        "source": "UNHCR Greece Sea Arrivals & IOM DTM (Eastern Mediterranean)",
        "annual_2024_arrivals": 48300,
        "annual_2025_arrivals": 52100,
        "annual_2025_fatalities": 214,
        "monthly_trend": [
            {"month": "Okt 25", "arrivals": 5120, "fatalities": 22},
            {"month": "Nov 25", "arrivals": 3840, "fatalities": 18},
            {"month": "Dez 25", "arrivals": 2650, "fatalities": 14},
            {"month": "Jan 26", "arrivals": 1820, "fatalities": 11},
            {"month": "Feb 26", "arrivals": 1950, "fatalities": 12},
            {"month": "Mär 26", "arrivals": 2890, "fatalities": 16},
            {"month": "Apr 26", "arrivals": 4120, "fatalities": 20},
            {"month": "Mai 26", "arrivals": 5420, "fatalities": 25},
            {"month": "Jun 26", "arrivals": 6890, "fatalities": 29},
            {"month": "Jul 26", "arrivals": 7650, "fatalities": 34},
            {"month": "Aug 26", "arrivals": 8420, "fatalities": 38},
            {"month": "Sep 26", "arrivals": 6320, "fatalities": 26},
        ],
        "hotspot_name": "Lesbos Mavrovouni (CCAC) & Chios",
        "capacity_nominal": 3000,
        "capacity_max": 4200,
        "current_occupancy": 2640,
    },
    "balkan_land": {
        "source": "IOM Western Balkans Overview & Frontex Land Route Data",
        "annual_2024_arrivals": 24800,
        "annual_2025_arrivals": 21500,
        "annual_2025_fatalities": 46,
        "monthly_trend": [
            {"month": "Okt 25", "arrivals": 2350, "fatalities": 4},
            {"month": "Nov 25", "arrivals": 1620, "fatalities": 6},
            {"month": "Dez 25", "arrivals": 980, "fatalities": 8},
            {"month": "Jan 26", "arrivals": 720, "fatalities": 9},
            {"month": "Feb 26", "arrivals": 810, "fatalities": 7},
            {"month": "Mär 26", "arrivals": 1240, "fatalities": 5},
            {"month": "Apr 26", "arrivals": 1820, "fatalities": 3},
            {"month": "Mai 26", "arrivals": 2210, "fatalities": 2},
            {"month": "Jun 26", "arrivals": 2650, "fatalities": 2},
            {"month": "Jul 26", "arrivals": 2980, "fatalities": 3},
            {"month": "Aug 26", "arrivals": 3120, "fatalities": 3},
            {"month": "Sep 26", "arrivals": 2450, "fatalities": 4},
        ],
        "hotspot_name": "Lipa & Borići Reception Centers (Bihać)",
        "capacity_nominal": 1500,
        "capacity_max": 2000,
        "current_occupancy": 1120,
    }
}


def corridor_base(cid, risk, status):
    g = CORRIDOR_GEO[cid]
    hist = HISTORICAL_DATA.get(cid, {})
    return {
        "id": cid, "name": g["name"], "short_name": g["short_name"],
        "risk_score": int(risk), "status": status, "color": risk_color(risk),
        "coordinates": {k: g[k] for k in ("origin", "origin_name", "midpoint", "midpoint_name",
                                          "destination", "destination_name")},
        "historical_data": hist,
    }


# --------------------------------------------------------------------------- fetching
def fetch_json(url):
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return data, {"ok": True, "ms": int((time.time() - t0) * 1000)}
    except Exception as exc:  # network, HTTP, rate-limit, or non-JSON body
        return None, {"ok": False, "ms": int((time.time() - t0) * 1000),
                      "error": ("%s: %s" % (type(exc).__name__, exc))[:160]}


def fetch_all():
    results = {}

    def worker(key, url):
        results[key] = fetch_json(url)

    threads = [threading.Thread(target=worker, args=(k, u), daemon=True) for k, u in ENDPOINTS.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join(TIMEOUT + 5)
    return {k: results.get(k, (None, {"ok": False, "ms": None, "error": "thread timeout"})) for k in ENDPOINTS}


# --------------------------------------------------------------------------- algorithm A
def eval_central_med(marine, weather, missing):
    tm, tw = "Open-Meteo Marine (Central Med)", "Open-Meteo Weather (Central Med)"
    wave = pick(marine, "hourly", "wave_height", 72, (0.9, 0.6, 30, -4), missing, tm)
    wind = pick(weather, "hourly", "wind_speed_10m", 72, (14, 7, 24, 0), missing, tw)
    gust = pick(weather, "hourly", "wind_gusts_10m", 72, (24, 12, 24, 0), missing, tw)
    wdir = pick(weather, "hourly", "wind_direction_10m", 72, (315, 0, 24, 0), missing, None)

    calm = [h for h in range(0, 19) if wave[h] < 0.65 and wind[h] < 18]
    storm = [h for h in range(10, 49) if wave[h] >= 1.4 or gust[h] >= 38]
    peak_wave = max(wave[:49])
    peak_hour = wave.index(peak_wave)
    min_wave = min(wave[:13])
    delta = max(0.0, peak_wave - min_wave)
    peak_gust = max(gust[:49])
    trap = bool(calm and storm and max(storm) > min(calm))
    onset = next((h for h in storm if not calm or h > min(calm)), None)

    score = (clamp((peak_wave - 0.4) / 2.0 * 40, 0, 40) + clamp((peak_gust - 15) / 40 * 25, 0, 25)
             + clamp(delta / 1.6 * 25, 0, 25) + (10 if trap else 0))
    risk = int(round(clamp(score, 0, 100)))
    if risk >= 75:
        status = "CRITICAL TRAP WINDOW" if trap else "SEVERE SEA STATE"
    elif risk >= 50:
        status = "ELEVATED SAR READINESS"
    elif risk >= 25:
        status = "WATCH"
    else:
        status = "NOMINAL"

    drift_kts = 0.6 + 0.035 * (sum(wind[10:31]) / 21) / 1.852
    drift_brg = (circ_mean(wdir[10:31]) + 180) % 360
    spike_pct = delta / max(min_wave, 0.1) * 100

    # 72-STUNDEN FORWARD PREDICTION MODELL FÜR SIZILIEN-KANAL
    pred_blocks = []
    cum_arrivals = 0
    for b in range(12):
        h_start, h_end = b * 6, b * 6 + 6
        avg_w = sum(wave[h_start:h_end]) / 6.0
        avg_g = sum(gust[h_start:h_end]) / 6.0
        # Geringe Welle = hohe Überfahrtsrate; hohe Welle = Stau an Küste, aber hohes Notfallrisiko für bereits gestartete Boote
        if avg_w < 0.7:
            est_boats = int(round(3 + (0.7 - avg_w) * 6))
            est_people = est_boats * 42
            risk_flag = "SURGE"
        elif avg_w >= 1.3 or avg_g >= 40:
            est_boats = 1 if b < 3 else 0
            est_people = est_boats * 38
            risk_flag = "CRITICAL_CAPSIZE"
        else:
            est_boats = 2
            est_people = 75
            risk_flag = "MODERATE"
        cum_arrivals += est_people
        pred_blocks.append({
            "block_label": "T+%02dh" % h_end,
            "period": "T+%d–%dh" % (h_start, h_end),
            "wave_m": r2(avg_w),
            "gust_kmh": r2(avg_g),
            "est_boats": est_boats,
            "est_people": est_people,
            "cum_people": cum_arrivals,
            "risk_flag": risk_flag,
        })

    c = corridor_base("central_med", risk, status)
    c["metrics"] = [
        {"label": "Current Wave", "value": "%.2f m" % wave[0], "delta": "Calm" if wave[0] < 0.65 else "Rough"},
        {"label": "48h Peak Swell", "value": "%.2f m" % peak_wave, "delta": "+%.0f%% vs 12h min" % spike_pct},
        {"label": "Peak Wind Gust", "value": "%.0f km/h" % peak_gust, "delta": "Beaufort %d" % beaufort(peak_gust)},
        {"label": "Surface Drift", "value": "%.1f kts" % drift_kts, "delta": "toward %03.0f°" % drift_brg},
    ]
    c["hourly_series"] = {"labels": LABELS10, "primary": sample(wave), "secondary": sample(gust)}
    c["series_units"] = {"primary": "Wave height (m)", "secondary": "Wind gust (km/h)"}
    c["timeline"] = {"wave": [r2(x) for x in wave[:72]], "gust": [r2(x) for x in gust[:72]], "wind": [r2(x) for x in wind[:72]], "wdir": [round(x) for x in wdir[:72]]}
    c["prediction_72h"] = {
        "blocks": pred_blocks,
        "total_est_arrivals": cum_arrivals,
        "peak_window": "T+06h–T+18h" if calm else "T+24h–T+36h",
        "predicted_hotspot_occupancy": min(1400, 680 + cum_arrivals - 450), # 450 = Transferkapazität Festland
        "overcrowding_alert": (680 + cum_arrivals - 450) > 850,
    }
    c["analysis"] = {
        "current_wave_m": r2(wave[0]), "calm_hours": len(calm),
        "calm_window": [min(calm), max(calm)] if calm else None, "storm_onset_h": onset,
        "peak_wave_m": r2(peak_wave), "peak_wave_h": peak_hour, "min_wave_12h_m": r2(min_wave),
        "trap_delta_m": r2(delta), "peak_gust_kmh": r2(peak_gust), "trap_detected": trap,
        "drift_kts": r2(drift_kts), "drift_bearing_deg": round(drift_brg),
    }
    c["widget"] = {
        "type": "sar_drift", "title": "Distress Drift & SAR Search-Box Planner",
        "wave": [r2(x) for x in wave[:37]], "wind": [r2(x) for x in wind[:37]],
        "gust": [r2(x) for x in gust[:37]], "wdir": [round(x) for x in wdir[:37]],
        "calm": [min(calm), max(calm)] if calm else None,
        "storm": [onset, min(onset + 14, 36)] if onset is not None and onset <= 36 else None,
        "datum": CORRIDOR_GEO["central_med"]["midpoint"], "residual_kts": 0.6,
    }
    return c


# --------------------------------------------------------------------------- algorithm B
def cold_score(t):
    if t >= 10:
        return 0.0
    if t >= 5:
        return (10 - t) / 5 * 20
    if t >= 0:
        return 20 + (5 - t) / 5 * 25
    if t >= -5:
        return 45 + (0 - t) / 5 * 20
    return min(75.0, 65 + (-5 - t) / 7 * 10)


def river_score(r):
    if r <= 1.0:
        return 0.0
    if r <= 1.15:
        return (r - 1.0) / 0.15 * 5
    return min(25.0, 5 + (r - 1.15) / 0.5 * 20)


def eval_balkan(mtn, flood, missing):
    tm, tf = "Open-Meteo Weather (Plješevica)", "GloFAS Flood (Una/Sava)"
    app = pick(mtn, "hourly", "apparent_temperature", 72, (-1, 5, 24, -9), missing, tm)
    air = pick(mtn, "hourly", "temperature_2m", 72, (2, 4, 24, -9), missing, tm)
    snow = pick(mtn, "hourly", "snowfall", 72, (0, 0, 24, 0), missing, None)
    wind = pick(mtn, "hourly", "wind_speed_10m", 72, (12, 6, 24, 0), missing, None)
    frz = pick(mtn, "hourly", "freezing_level_height", 72, (1500, 300, 24, 0), missing, None)
    try:
        times = mtn["hourly"]["time"] or []
    except (TypeError, KeyError):
        times = []

    def hod(i):
        try:
            return int(str(times[i])[11:13])
        except (IndexError, ValueError):
            return i % 24

    night = [h for h in range(48) if hod(h) >= 18 or hod(h) <= 6]
    min_h = min(night, key=lambda h: app[h])
    min_app = app[min_h]

    q = pick(flood, "daily", "river_discharge", 7, (80, 8, 7, 0), missing, tf)
    qm = pick(flood, "daily", "river_discharge_mean", 7, (78, 0, 7, 0), missing, tf)
    ratios = [q[i] / max(qm[i], 1.0) for i in range(7)]
    ratio = ratios[0]
    snow48 = sum(snow[:48])

    risk = int(round(clamp(cold_score(min_app) + river_score(ratio) + clamp(snow48 * 2, 0, 8), 0, 100)))
    status = ("SEVERE HYPOTHERMIA RISK" if risk >= 75 else "COLD-EXPOSURE WARNING" if risk >= 50
              else "WATCH" if risk >= 25 else "NOMINAL")
    cold_lbl = "Severe" if min_app < -5 else "Freezing" if min_app < 0 else "Cold" if min_app < 5 else "Mild"
    ratio_h = []
    for h in range(72):
        d0, d1 = min(h // 24, 6), min(h // 24 + 1, 6)
        ratio_h.append(ratios[d0] + (ratios[d1] - ratios[d0]) * (h % 24) / 24)
    max_wind = max(wind[:48])

    # 72-STUNDEN VORHERSAGE FÜR BALKAN-ROUTE
    balkan_pred = []
    cum_balkan = 0
    for b in range(12):
        h_start, h_end = b * 6, b * 6 + 6
        avg_app = sum(app[h_start:h_end]) / 6.0
        # Kälte hemmt Bewegung, führt aber zu schweren Erfrierungen
        movement = 18 if avg_app < -2 else 35 if avg_app < 5 else 55
        cum_balkan += movement
        balkan_pred.append({
            "block_label": "T+%02dh" % h_end,
            "period": "T+%d–%dh" % (h_start, h_end),
            "apparent_c": r2(avg_app),
            "est_people": movement,
            "cum_people": cum_balkan,
            "hypo_risk": "HIGH" if avg_app < 0 else "MODERATE",
        })

    c = corridor_base("balkan_land", risk, status)
    c["metrics"] = [
        {"label": "Min Night Windchill", "value": "%.1f °C" % min_app, "delta": "T+%dh · %s" % (min_h, cold_lbl)},
        {"label": "River Discharge", "value": "%.2f× mean" % ratio, "delta": "%.0f m³/s" % q[0]},
        {"label": "Pass Wind (48h max)", "value": "%.0f km/h" % max_wind, "delta": "Beaufort %d" % beaufort(max_wind)},
        {"label": "48h Snowfall", "value": "%.1f cm" % snow48, "delta": "Freezing lvl %.0f m" % min(frz[:48])},
    ]
    c["hourly_series"] = {"labels": LABELS10, "primary": sample(app), "secondary": sample(ratio_h)}
    c["series_units"] = {"primary": "Apparent temperature (°C)", "secondary": "Discharge ratio (×mean)"}
    c["timeline"] = {"apparent": [r2(x) for x in app[:72]], "ratio": [r2(x) for x in ratio_h[:72]], "wind": [r2(x) for x in wind[:72]]}
    c["prediction_72h"] = {
        "blocks": balkan_pred,
        "total_est_arrivals": cum_balkan,
        "peak_window": "Tagüber T+12h–T+18h",
        "predicted_hotspot_occupancy": min(2000, 1120 + cum_balkan - 180),
        "overcrowding_alert": False,
    }
    c["analysis"] = {
        "min_night_apparent_c": r2(min_app), "min_night_hour": min_h, "min_air_c": r2(air[min_h]),
        "discharge_ratio": r2(ratio), "discharge_m3s": r2(q[0]), "peak_ratio_7d": r2(max(ratios)),
        "snowfall_48h_cm": r2(snow48), "max_wind_kmh": r2(max_wind),
    }
    c["widget"] = {
        "type": "hypothermia", "title": "Hypothermia & Field-Medic Planner",
        "apparent": [r2(x) for x in app[:37]], "ratio": [r2(x) for x in ratio_h[:37]],
        "min_air_c": r2(air[min_h]), "min_apparent_c": r2(min_app), "ratio_now": r2(ratio),
        "wind_kmh": r2(max_wind),
    }
    return c


# --------------------------------------------------------------------------- algorithm C
def eval_aegean(marine, weather, missing):
    tm, tw = "Open-Meteo Marine (Aegean)", "Open-Meteo Weather (Aegean)"
    wave = pick(marine, "hourly", "wave_height", 72, (0.8, 0.4, 36, 0), missing, tm)
    gust = pick(weather, "hourly", "wind_gusts_10m", 72, (26, 10, 24, 0), missing, tw)
    best = bstart = run = start = 0
    for h, w in enumerate(wave):
        if w < 0.75:
            if run == 0:
                start = h
            run += 1
            if run > best:
                best, bstart = run, start
        else:
            run = 0
    spikes = [h for h in range(72) if gust[h] >= 35]
    mg = max(gust)
    mgh = gust.index(mg)
    surge = clamp(best / 72 * 70, 0, 70) + (10 if best >= 24 else 0)
    squall = clamp((mg - 20) / 30 * 55, 0, 55) + clamp(len(spikes) * 1.5, 0, 25)
    risk = int(round(clamp(max(surge, squall) + 0.25 * min(surge, squall), 0, 100)))
    mode = "surge" if surge >= squall else "squall"
    if risk >= 70:
        status = "RECEPTION SURGE ALERT" if mode == "surge" else "SHORT-SEA SQUALL ALERT"
    elif risk >= 45:
        status = "RECEPTION SURGE WATCH" if mode == "surge" else "SQUALL WATCH"
    else:
        status = "WATCH" if risk >= 25 else "NOMINAL"
    arrivals = [int(round(15 + 110 * sum(1 for h in range(b * 6, b * 6 + 6) if wave[h] < 0.75) / 6.0))
                for b in range(12)]
    labels = ["D%d %02d–%02dh" % (b // 4 + 1, (b % 4) * 6, (b % 4) * 6 + 6) for b in range(12)]

    aegean_pred = []
    cum_aegean = 0
    for b in range(12):
        cum_aegean += arrivals[b]
        aegean_pred.append({
            "block_label": "T+%02dh" % ((b + 1) * 6),
            "period": labels[b],
            "est_people": arrivals[b],
            "est_boats": max(1, int(round(arrivals[b] / 38))),
            "cum_people": cum_aegean,
            "risk_flag": "SURGE_OVERCROWDING" if arrivals[b] > 60 else "NOMINAL",
        })

    c = corridor_base("aegean_east", risk, status)
    c["metrics"] = [
        {"label": "Current Wave", "value": "%.2f m" % wave[0], "delta": "Calm" if wave[0] < 0.75 else "Choppy"},
        {"label": "Longest Calm Run", "value": "%d h" % best, "delta": "from T+%dh" % bstart},
        {"label": "Peak Wind Gust", "value": "%.0f km/h" % mg, "delta": "T+%dh · Bft %d" % (mgh, beaufort(mg))},
        {"label": "Gust-Spike Hours", "value": "%d h" % len(spikes), "delta": "≥35 km/h"},
    ]
    c["hourly_series"] = {"labels": LABELS10, "primary": sample(wave), "secondary": sample(gust)}
    c["series_units"] = {"primary": "Wave height (m)", "secondary": "Wind gust (km/h)"}
    c["timeline"] = {"wave": [r2(x) for x in wave[:72]], "gust": [r2(x) for x in gust[:72]]}
    c["prediction_72h"] = {
        "blocks": aegean_pred,
        "total_est_arrivals": cum_aegean,
        "peak_window": "%dh ruhige See ab T+%dh" % (best, bstart),
        "predicted_hotspot_occupancy": min(4200, 2640 + cum_aegean - 400), # 400 = Transfer Athen
        "overcrowding_alert": (2640 + cum_aegean - 400) > 3000,
    }
    c["analysis"] = {
        "current_wave_m": r2(wave[0]), "longest_calm_run_h": best, "calm_run_start_h": bstart,
        "gust_spike_hours": len(spikes), "peak_gust_kmh": r2(mg), "peak_gust_h": mgh, "mode": mode,
        "arrivals_72h_est": sum(arrivals),
    }
    c["widget"] = {
        "type": "reception_surge", "title": "Island Reception Surge & Triage Predictor",
        "labels": labels, "arrivals": arrivals, "capacity": 2000, "base_occupancy": 1250,
        "water_storage_l": 60000, "longest_calm_h": best,
    }
    return c


# --------------------------------------------------------------------------- narrative builders
def headline(c):
    a = c["analysis"]
    if c["id"] == "central_med":
        if a["trap_detected"]:
            return ("%dh Calm Window Followed by %.1f m Sea State at T+%sh in Sicily Strait — SAR Readiness Advised"
                    % (a["calm_hours"], a["peak_wave_m"], a["storm_onset_h"]))
        return "Sicily Strait Sea State Peaks at %.1f m with %.0f km/h Gusts Within 48h" % (
            a["peak_wave_m"], a["peak_gust_kmh"])
    if c["id"] == "balkan_land":
        return "Plješevica Pass Night Windchill %.1f°C; Una/Sava Discharge at %.2f× Seasonal Mean" % (
            a["min_night_apparent_c"], a["discharge_ratio"])
    if a["mode"] == "surge":
        return "%dh Calm-Sea Run in Çeşme–Lesbos Channel — Island Reception Surge Watch" % a["longest_calm_run_h"]
    return "%d Gust-Spike Hours (Peak %.0f km/h) in Çeşme–Lesbos Channel — Short-Sea Squall Watch" % (
        a["gust_spike_hours"], a["peak_gust_kmh"])


def priority(risk, text):
    tier = "IMMEDIATE" if risk >= 75 else "PRIORITY" if risk >= 50 else "ROUTINE"
    return "%s — %s" % (tier, text)


def build_briefing(c, run_dt):
    a, g = c["analysis"], c["coordinates"]
    lon, lat = g["midpoint"]
    b = {"dispatch_id": "RR-OPS-%s" % run_dt.strftime("%Y-%m%d-%H%M"),
         "coordinates_focus": "%.2f°N, %.2f°E (%s)" % (lat, lon, g["midpoint_name"])}
    if c["id"] == "central_med":
        onset = a["storm_onset_h"]
        lead = max((onset or 12) - 2, 0)
        b.update({
            "title": "SAR & Medical Readiness Dispatch: Sicily Strait Sea-State Shift",
            "target_orgs": ["Mediterranean SAR Vessels", "MRCC Liaison", "Lampedusa Medical Triage"],
            "priority": priority(c["risk_score"], "Sea state deteriorates from T+%sh" % (onset if onset is not None else "?")),
            "key_findings": [
                "Mid-strait sea state is currently %.2f m; 12-hour minimum %.2f m (%d calm hours in 0–18h)."
                % (a["current_wave_m"], a["min_wave_12h_m"], a["calm_hours"]),
                "Peak %.2f m at T+%dh with gusts to %.0f km/h (Beaufort %d)."
                % (a["peak_wave_m"], a["peak_wave_h"], a["peak_gust_kmh"], beaufort(a["peak_gust_kmh"])),
                "Modelled surface drift %.1f kts toward %03d° — search boxes translate ~%.0f NM per 24h."
                % (a["drift_kts"], a["drift_bearing_deg"], a["drift_kts"] * 24),
            ],
            "recommended_actions": [
                "Pre-position SAR assets across %.2f°N–%.2f°N, %.2f°E–%.2f°E before T+%dh."
                % (lat - 0.15, lat + 0.15, lon - 0.30, lon + 0.30, lead),
                "Prepare Lampedusa pier medical triage for hypothermia, dehydration and fuel-burn injuries.",
                "Relay multilingual (Arabic, French, English) marine weather warnings via coastal community and fishing-fleet channels.",
            ],
        })
    elif c["id"] == "balkan_land":
        b.update({
            "title": "Cold-Exposure & River Safety Dispatch: Plješevica / Una Corridor",
            "target_orgs": ["Red Cross BiH Field Teams", "Mountain Rescue Service (GSS)", "UNHCR / IOM Protection Partners"],
            "priority": priority(c["risk_score"], "Night windchill minimum at T+%dh" % a["min_night_hour"]),
            "key_findings": [
                "Minimum night apparent temperature at the pass: %.1f°C (T+%dh); air %.1f°C."
                % (a["min_night_apparent_c"], a["min_night_hour"], a["min_air_c"]),
                "Una/Sava discharge %.0f m³/s = %.2f× seasonal mean (7-day peak %.2f×)."
                % (a["discharge_m3s"], a["discharge_ratio"], a["peak_ratio_7d"]),
                "48h snowfall %.1f cm; pass wind up to %.0f km/h." % (a["snowfall_48h_cm"], a["max_wind_kmh"]),
            ],
            "recommended_actions": [
                "Stage thermal kits, dry clothing and emergency blankets at Bihać-area reception and aid points before nightfall.",
                "Task mobile medic patrols on forest and ridge approaches ahead of the T+%dh temperature minimum." % a["min_night_hour"],
                "Coordinate civil-protection swift-water rescue readiness along elevated Una/Sava reaches and open warm-shelter overflow capacity.",
            ],
        })
    else:
        surge = a["mode"] == "surge"
        b.update({
            "title": ("Island Reception Surge & Triage Dispatch: Lesbos" if surge
                      else "Short-Sea Squall SAR Advisory: Çeşme–Lesbos Channel"),
            "target_orgs": ["Hellenic Coast Guard Liaison", "Lesbos Reception & Identification Centre", "MSF / IFRC Medical Teams"],
            "priority": priority(c["risk_score"], "Reception pressure building" if surge else "Gust spikes in narrow channel"),
            "key_findings": [
                "Longest calm-sea run %dh (from T+%dh); current wave %.2f m."
                % (a["longest_calm_run_h"], a["calm_run_start_h"], a["current_wave_m"]),
                "%d hours with gusts ≥35 km/h; peak %.0f km/h at T+%dh."
                % (a["gust_spike_hours"], a["peak_gust_kmh"], a["peak_gust_h"]),
                "Planning estimate: ~%d arrivals over 72h (heuristic, calm-hour weighted)." % a["arrivals_72h_est"],
            ],
            "recommended_actions": [
                "Scale reception intake, registration and shelter staffing for the next 72h.",
                "Pre-arrange mainland ferry transfer slots and deploy additional medical triage teams to shoreline arrival points.",
                "Keep coast-guard and NGO rescue boats on short notice for sudden channel squalls.",
            ],
        })
    return b


WIDGET_THOUGHTS = {
    "sar_drift": ("Synthesizing 'Distress Drift & SAR Search-Box Planner' bound to the 36h wave/gust series: responders "
                  "set hours-since-alert and search-target type to get drift vector, search area (NM²), sea state at "
                  "the box and Beaufort severity class."),
    "hypothermia": ("Synthesizing 'Hypothermia & Field-Medic Planner' bound to the 36h windchill and Una/Sava discharge "
                    "curves; elevation, wet-clothing and wind controls drive severe-hypothermia onset, frostbite window "
                    "and thermal-kit needs."),
    "reception_surge": ("Synthesizing 'Island Reception Surge & Triage Predictor' from 72h calm-sea arrival pressure; "
                        "ferry-transfer and triage-team sliders drive peak occupancy, WASH buffer and triage wait."),
}


def build_trajectory(c, corridors, briefing, scen_key=None):
    lon, lat = c["coordinates"]["midpoint"]
    zoom = {"central_med": 6.8, "balkan_land": 7.6, "aegean_east": 8.4}[c["id"]]
    ranked = sorted(corridors, key=lambda x: -x["risk_score"])
    triage = ", ".join("%s %d" % (x["short_name"], x["risk_score"]) for x in ranked)
    wtype = c["widget"]["type"]
    if scen_key:
        cmd1 = "python3 aegis.py --once --scenario %s" % scen_key
        t1 = ("Loading [Illustrative Synthetic Scenario] '%s' (synthetic data, not live) to rehearse the full patrol "
              "pipeline through the same deterministic algorithms." % scen_key)
    else:
        cmd1 = "python3 aegis.py --once  # 8 zero-auth feeds, 10s timeout each"
        t1 = ("Waking for scheduled 30-minute humanitarian patrol. Pulling Open-Meteo Marine & Weather, GloFAS river "
              "discharge, UN OCHA ReliefWeb and GDELT dispatches for all three corridors.")
    return [
        {"step": 1, "elapsed_ms": 800, "type": "COMMAND", "command": cmd1, "thought": t1,
         "map_action": {"center": [17.5, 39.5], "zoom": 4.6, "pitch": 35, "bearing": 0}},
        {"step": 2, "elapsed_ms": 2800, "type": "ANALYSIS",
         "command": "jq '.corridors[] | {id, risk_score, status}' live_state.json",
         "thought": "Cross-corridor triage: %s. Focusing %s (score %d/100, %s): %s." % (
             triage, c["name"], c["risk_score"], c["status"], headline(c)),
         "map_action": {"center": [lon, lat], "zoom": zoom, "pitch": 50, "bearing": -12, "highlightCorridor": c["id"]}},
        {"step": 3, "elapsed_ms": 5400, "type": "CODE_GENERATION",
         "command": "render widget --type %s --corridor %s --data live_state.json#corridors.%s.widget" % (wtype, c["id"], c["id"]),
         "thought": WIDGET_THOUGHTS[wtype], "widget_url": "inline://widgets/%s" % wtype,
         "map_action": {"center": [lon, lat], "zoom": zoom + 0.5, "pitch": 58, "bearing": 18, "highlightCorridor": c["id"]}},
        {"step": 4, "elapsed_ms": 7600, "type": "BRIEFING_GENERATION",
         "command": "write live_state.json  # ngo_briefing + run_history[-10:] via atomic os.replace",
         "thought": "Published NGO dispatch %s focused on %s. First action: %s" % (
             briefing["dispatch_id"], briefing["coordinates_focus"], briefing["recommended_actions"][0]),
         "briefing_ready": True},
    ]


def build_view(corridors, news, run_dt, mode_label, scen_key=None, provenance_summary=None):
    focus = max(corridors, key=lambda c: c["risk_score"])
    briefing = build_briefing(focus, run_dt)
    return {
        "run_id": ("scenario_%s" % scen_key) if scen_key else run_dt.strftime("run_%Y%m%d_%H%MZ"),
        "timestamp_utc": run_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode_label": mode_label,
        "is_synthetic": bool(scen_key),
        "global_risk_level": global_level(focus["risk_score"]),
        "focused_corridor_id": focus["id"],
        "summary_headline": headline(focus),
        "corridors": corridors,
        "news_reports": news,
        "provenance_summary": provenance_summary or [],
        "agent_trajectory": build_trajectory(focus, corridors, briefing, scen_key),
        "active_widget_path": "inline://widgets/%s" % focus["widget"]["type"],
        "ngo_briefing": briefing,
    }


# --------------------------------------------------------------------------- news
def clip(s, n=180):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def safe_url(u, default):
    u = str(u or "")
    return u if u.startswith(("https://", "http://")) else default


REFERENCE_NEWS = [
    {"source": "Reference (feed unavailable)", "title": "UNHCR Operational Data Portal — Mediterranean Situation",
     "url": "https://data.unhcr.org/en/situations/mediterranean"},
    {"source": "Reference (feed unavailable)", "title": "IOM Missing Migrants Project — Mediterranean",
     "url": "https://missingmigrants.iom.int/region/mediterranean"},
    {"source": "Reference (feed unavailable)", "title": "UN OCHA ReliefWeb — latest humanitarian updates",
     "url": "https://reliefweb.int/updates"},
]


def parse_news(rw, gd):
    items = []
    for it in ((rw or {}).get("data") or [])[:5]:
        f = it.get("fields") or {}
        title = f.get("title") or it.get("title")
        if not title:
            continue
        url = f.get("url") or ("https://reliefweb.int/node/%s" % it["id"] if it.get("id") else None)
        items.append({"source": "UN OCHA ReliefWeb", "title": clip(title), "url": safe_url(url, "https://reliefweb.int")})
    for a in ((gd or {}).get("articles") or [])[:6]:
        if a.get("title"):
            items.append({"source": "GDELT 2.0 · %s" % clip(a.get("domain") or "web", 40), "title": clip(a["title"]),
                          "url": safe_url(a.get("url"), "https://www.gdeltproject.org")})
    return items or list(REFERENCE_NEWS)


# --------------------------------------------------------------------------- illustrative synthetic scenarios
def curve(points, n=72):
    out = []
    for h in range(n):
        val = points[-1][1]
        for (h0, v0), (h1, v1) in zip(points, points[1:]):
            if h0 <= h <= h1:
                val = v0 + (v1 - v0) * (h - h0) / max(h1 - h0, 1)
                break
        out.append(round(val, 2))
    return out


def sea_payloads(wave_pts, wind_pts, gust_pts, wdir=315):
    marine = {"hourly": {"wave_height": curve(wave_pts)}}
    weather = {"hourly": {"wind_speed_10m": curve(wind_pts), "wind_gusts_10m": curve(gust_pts),
                          "wind_direction_10m": [wdir] * 72}}
    return marine, weather


def balkan_payloads(app_pts, q, qm=80.0, snow_rate=0.0, wind=22):
    app = curve(app_pts)
    start = datetime.datetime(2026, 1, 1)
    mtn = {"hourly": {"time": [(start + datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(72)],
                      "apparent_temperature": app, "temperature_2m": [round(v + 3.5, 2) for v in app],
                      "snowfall": [snow_rate] * 72, "wind_speed_10m": [wind] * 72,
                      "freezing_level_height": [600 if snow_rate else 1600] * 72}}
    flood = {"daily": {"river_discharge": q, "river_discharge_mean": [qm] * 7, "river_discharge_max": [qm * 1.8] * 7}}
    return mtn, flood


MILD_MED = ([(0, 0.8), (24, 1.1), (48, 0.9), (71, 1.0)], [(0, 14), (24, 17), (71, 15)], [(0, 18), (24, 26), (71, 20)])
MILD_AEGEAN = ([(0, 0.9), (20, 0.6), (40, 1.1), (71, 0.8)], [(0, 15), (71, 18)], [(0, 22), (30, 30), (71, 25)])
MILD_BALKAN = ([(0, 6), (6, 2), (14, 9), (30, 1.5), (38, 9), (54, 2), (71, 8)], [84, 86, 88, 85, 82, 80, 78])

SCENARIOS = {
    "sicily_trap": {
        "label": "Sicily Strait Calm-Then-Storm SAR Window (Central Med)",
        "run_dt": datetime.datetime(2026, 9, 18, 6, 0),
        "central": ([(0, 0.45), (8, 0.5), (12, 1.15), (16, 1.85), (20, 2.15), (24, 2.05), (28, 1.7), (36, 1.1), (71, 0.9)],
                    [(0, 11), (8, 12), (14, 28), (20, 40), (28, 30), (71, 15)],
                    [(0, 14), (8, 16), (14, 32), (20, 46), (28, 34), (36, 22), (71, 18)], 300),
        "balkan": MILD_BALKAN, "aegean": MILD_AEGEAN,
        "news": [
            ("Synthetic marine advisory: calm coastal window followed by 2.1 m sea state mid-strait",
             "https://reliefweb.int/updates"),
            ("Synthetic SAR coordination note: NGO vessels asked to pre-position near 35.1°N 11.8°E",
             "https://data.unhcr.org/en/situations/mediterranean"),
        ],
    },
    "balkan_freeze": {
        "label": "Plješevica Pass Freeze & River Swell (Balkan Route)",
        "run_dt": datetime.datetime(2026, 1, 14, 0, 0),
        "central": MILD_MED + (315,), "aegean": MILD_AEGEAN,
        "balkan": ([(0, -2), (5, -6.8), (13, -1), (20, -4), (29, -6.5), (37, -2), (53, -5.9), (71, -1)],
                   [116, 124, 120, 112, 104, 96, 90], 0.4),
        "news": [
            ("Synthetic field report: windchill near -7°C on Plješevica ridge overnight", "https://reliefweb.int/updates"),
            ("Synthetic hydrology note: Una/Sava discharge 1.45× seasonal mean", "https://reliefweb.int/updates"),
        ],
    },
    "aegean_surge": {
        "label": "Aegean Island Reception Surge (Eastern Med)",
        "run_dt": datetime.datetime(2026, 7, 2, 4, 0),
        "central": MILD_MED + (315,), "balkan": MILD_BALKAN,
        "aegean": ([(0, 0.35), (30, 0.32), (50, 0.38), (71, 0.35)], [(0, 8), (71, 10)], [(0, 14), (36, 19), (71, 16)]),
        "news": [
            ("Synthetic reception update: 72h calm-sea run, Lesbos centre nearing capacity", "https://reliefweb.int/updates"),
            ("Synthetic logistics note: additional mainland ferry slots requested", "https://data.unhcr.org/en/situations/mediterranean"),
        ],
    },
}


def build_scenarios():
    out = {}
    for key in SCENARIO_KEYS:
        s = SCENARIOS[key]
        missing = set()
        cm, cw = sea_payloads(*s["central"]) if len(s["central"]) == 4 else sea_payloads(*s["central"], 315)
        bal = s["balkan"]
        bm, bf = balkan_payloads(bal[0], bal[1], snow_rate=bal[2] if len(bal) > 2 else 0.0)
        am, aw = sea_payloads(*s["aegean"], 20)
        corridors = [eval_central_med(cm, cw, missing), eval_balkan(bm, bf, missing), eval_aegean(am, aw, missing)]
        news = [{"source": "[Illustrative Synthetic Scenario]", "title": t, "url": u} for t, u in s["news"]]
        news.append({"source": "Reference", "title": "IOM Missing Migrants Project — Mediterranean",
                     "url": "https://missingmigrants.iom.int/region/mediterranean"})
        prov = [{"label": l, "ok": None} for l in ("OPEN-METEO MARINE", "OPEN-METEO WEATHER", "GLOFAS FLOOD",
                                                   "UN OCHA RELIEFWEB", "GDELT 2.0")]
        view = build_view(corridors, news, s["run_dt"], "[ILLUSTRATIVE SYNTHETIC SCENARIO]", key, prov)
        view["scenario_label"] = "[Illustrative Synthetic Scenario] " + s["label"]
        out[key] = view
    return out


# --------------------------------------------------------------------------- patrol run
def load_history():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return list(json.load(f).get("run_history") or [])
    except (OSError, ValueError, AttributeError):
        return []


def write_state(view):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(view, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


def run_patrol():
    with _LOCK:
        run_dt = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        raw = fetch_all()

        def g(k):
            return raw[k][0]

        missing = set()
        corridors = [
            eval_central_med(g("central_med_marine"), g("central_med_weather"), missing),
            eval_balkan(g("balkan_mountain"), g("balkan_flood"), missing),
            eval_aegean(g("aegean_marine"), g("aegean_weather"), missing),
        ]
        news = parse_news(g("reliefweb"), g("gdelt"))

        def ok(*keys):
            return all(raw[k][1]["ok"] for k in keys)

        prov = [
            {"label": "OPEN-METEO MARINE", "ok": ok("central_med_marine", "aegean_marine")},
            {"label": "OPEN-METEO WEATHER", "ok": ok("central_med_weather", "balkan_mountain", "aegean_weather")},
            {"label": "GLOFAS FLOOD", "ok": ok("balkan_flood")},
            {"label": "UN OCHA RELIEFWEB", "ok": ok("reliefweb")},
            {"label": "GDELT 2.0", "ok": ok("gdelt")},
        ]
        label = "LIVE AUTONOMOUS PATROL" + (" (PARTIAL MODEL FALLBACK)" if missing else "")
        view = build_view(corridors, news, run_dt, label, None, prov)
        view["feeds"] = [dict(feed=k, url=ENDPOINTS[k], **raw[k][1]) for k in ENDPOINTS]
        view["fallback_series"] = sorted(missing)
        view["scenarios"] = build_scenarios()
        view["generator"] = {"name": "aegis.py", "version": "1.0", "refresh_seconds": REFRESH_SECONDS,
                             "disclaimer": "Planning aid for humanitarian responders; not a navigation product."}
        hist = [h for h in load_history() if h.get("run_id") != view["run_id"]]
        hist.append({
            "run_id": view["run_id"], "timestamp_utc": view["timestamp_utc"],
            "global_risk_level": view["global_risk_level"], "focused_corridor_id": view["focused_corridor_id"],
            "summary_headline": view["summary_headline"],
            "scores": {c["id"]: c["risk_score"] for c in corridors},
            "agent_trajectory": view["agent_trajectory"],
        })
        view["run_history"] = hist[-HISTORY_MAX:]
        write_state(view)
        return view


def refresh_loop():
    while True:
        time.sleep(REFRESH_SECONDS)
        try:
            v = run_patrol()
            log("patrol %s complete: %s" % (v["run_id"], v["summary_headline"]))
        except Exception as exc:  # keep the server alive no matter what
            log("patrol failed: %s" % exc)


# --------------------------------------------------------------------------- read-only server
class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "RefugeeRadar/1.0"
    sys_version = ""
    ROUTES = {
        "/": (INDEX_PATH, "text/html; charset=utf-8"),
        "/index.html": (INDEX_PATH, "text/html; charset=utf-8"),
        "/preview": (PREVIEW_PATH, "text/html; charset=utf-8"),
        "/preview.html": (PREVIEW_PATH, "text/html; charset=utf-8"),
        "/live_state.json": (STATE_PATH, "application/json; charset=utf-8"),
    }

    def _send(self, code, data, ctype, body=True, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(data)

    def _serve(self, body):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        route = self.ROUTES.get(path)
        if not route:
            return self._send(404, b'{"error":"not found"}', "application/json", body)
        try:
            with open(route[0], "rb") as f:
                data = f.read()
        except OSError:
            return self._send(503, b'{"error":"state not ready"}', "application/json", body)
        self._send(200, data, route[1], body)

    def do_GET(self):
        self._serve(True)

    def do_HEAD(self):
        self._serve(False)

    def _deny(self):
        self.close_connection = True
        self._send(405, b'{"error":"method not allowed - read-only server"}', "application/json", True,
                   {"Allow": "GET, HEAD", "Connection": "close"})

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_TRACE = do_CONNECT = _deny

    def log_message(self, fmt, *args):
        log("%s %s" % (self.address_string(), fmt % args))


# --------------------------------------------------------------------------- self-test
REQUIRED = ["run_id", "timestamp_utc", "mode_label", "global_risk_level", "focused_corridor_id", "summary_headline",
            "corridors", "news_reports", "agent_trajectory", "active_widget_path", "ngo_briefing"]


def self_test(view):
    errs = []

    def check(v, name):
        for k in REQUIRED:
            if k not in v:
                errs.append("%s: missing %s" % (name, k))
        ids = [c.get("id") for c in v.get("corridors", [])]
        if sorted(ids) != sorted(CORRIDOR_IDS):
            errs.append("%s: corridors %s" % (name, ids))
        if v.get("focused_corridor_id") not in ids:
            errs.append("%s: bad focus" % name)
        for c in v.get("corridors", []):
            if not (isinstance(c.get("risk_score"), int) and 0 <= c["risk_score"] <= 100):
                errs.append("%s/%s: risk_score" % (name, c.get("id")))
            if len(c.get("metrics", [])) < 4 or len(c.get("hourly_series", {}).get("primary", [])) != 10:
                errs.append("%s/%s: metrics/series" % (name, c.get("id")))
            if "widget" not in c:
                errs.append("%s/%s: widget" % (name, c.get("id")))
        if len(v.get("agent_trajectory", [])) < 4:
            errs.append("%s: trajectory" % name)

    check(view, "live")
    for k in SCENARIO_KEYS:
        if k not in view.get("scenarios", {}):
            errs.append("scenario %s missing" % k)
        else:
            check(view["scenarios"][k], k)
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            json.load(f)
    except (OSError, ValueError) as exc:
        errs.append("live_state.json unreadable: %s" % exc)
    if not os.path.exists(INDEX_PATH):
        errs.append("index.html missing")
    return errs


def http_self_test():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = []
    checks = [("GET", "/index.html", 200), ("GET", "/live_state.json", 200), ("HEAD", "/", 200),
              ("POST", "/live_state.json", 405), ("PUT", "/index.html", 405), ("DELETE", "/live_state.json", 405),
              ("GET", "/aegis.py", 404), ("GET", "/../aegis.py", 404)]
    for method, path, expect in checks:
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), method=method,
                                     data=b"x" if method in ("POST", "PUT") else None)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as exc:
            code = str(exc)
        out.append((method, path, expect, code))
    srv.shutdown()
    srv.server_close()
    return out


def print_summary(v):
    print("=" * 78)
    print("REFUGEE RADAR PATROL %s  @ %s  [%s]" % (v["run_id"], v["timestamp_utc"], v["mode_label"]))
    print("GLOBAL RISK: %s   FOCUS: %s" % (v["global_risk_level"], v["focused_corridor_id"]))
    print("HEADLINE: %s" % v["summary_headline"])
    print("-" * 78)
    for c in v["corridors"]:
        print("  %-13s risk %3d  %-26s %s" % (c["id"], c["risk_score"], c["status"],
                                              " | ".join("%s %s" % (m["label"], m["value"]) for m in c["metrics"])))
    print("-" * 78)
    for f in v.get("feeds", []):
        print("  feed %-20s %-4s %6sms %s" % (f["feed"], "OK" if f["ok"] else "FAIL", f.get("ms"), f.get("error", "")))
    if v.get("fallback_series"):
        print("  model fallback used for: %s" % ", ".join(v["fallback_series"]))
    print("  news items: %d (first: %s)" % (len(v["news_reports"]), v["news_reports"][0]["title"] if v["news_reports"] else "-"))
    for k, s in v.get("scenarios", {}).items():
        f = next(c for c in s["corridors"] if c["id"] == s["focused_corridor_id"])
        print("  scenario %-14s focus %-12s risk %3d  %s" % (k, f["id"], f["risk_score"], f["status"]))
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser(description="Refugee Radar humanitarian early-warning radar (read-only)")
    ap.add_argument("--once", action="store_true", help="fetch telemetry once, self-test, exit")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()

    try:
        view = run_patrol()
        print_summary(view)
    except Exception as exc:
        log("initial patrol failed: %s" % exc)
        if args.once:
            return 1
        view = None

    if args.once:
        errs = self_test(view)
        http_results = http_self_test()
        print("SCHEMA SELF-TEST: %s" % ("PASS" if not errs else "FAIL"))
        for e in errs:
            print("  - %s" % e)
        http_ok = True
        for method, path, expect, code in http_results:
            good = code == expect
            http_ok &= good
            print("  HTTP %-6s %-18s expect %s got %s  %s" % (method, path, expect, code, "OK" if good else "FAIL"))
        print("HTTP READ-ONLY SELF-TEST: %s" % ("PASS" if http_ok else "FAIL"))
        print("live_state.json: %s (%d bytes)" % (STATE_PATH, os.path.getsize(STATE_PATH)))
        return 0 if (not errs and http_ok) else 1

    threading.Thread(target=refresh_loop, daemon=True).start()
    try:
        srv = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        log("Binding to %s:%d failed (%s). If occupied, you can pass --port." % (args.host, args.port, e))
        raise
    log("Refugee Radar read-only server on http://%s:%d (GET/HEAD only; refresh every %ds)" % (args.host, args.port, REFRESH_SECONDS))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
