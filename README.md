# Refugee Radar (AEGIS)

> **Autonomous Humanitarian & SAR Early-Warning Situational Awareness System**  
> *Zero-auth real-time telemetry fusion, 72-hour route-adaptive predictive models, and tactical IAMSAR leeway drift calculation for humanitarian responders and civil search & rescue.*

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B%20(Stdlib%20Only)-success.svg)](aegis.py)
[![Frontend: MapLibre GL](https://img.shields.io/badge/Frontend-MapLibre%20GL%20%7C%20Vanilla%20JS-informational.svg)](index.html)
[![Live Demo](https://img.shields.io/badge/Live%20Deployment-Cloudflare%20Edge-brightgreen.svg)](https://evening-barbara-displaying-affordable.trycloudflare.com)
[![Status: Operational](https://img.shields.io/badge/Status-Operational%20MVP-orange.svg)](#)

---

### 🌐 Live Deployment & Preview

* **Public Live Instance:** [https://evening-barbara-displaying-affordable.trycloudflare.com](https://evening-barbara-displaying-affordable.trycloudflare.com)
* **Local Endpoint:** `http://127.0.0.1:8081` (or `:8080`)

---

## 1. Executive Summary & Purpose

**Refugee Radar** is an open-source, non-commercial civil situational awareness dashboard built for humanitarian logistical readiness, Search and Rescue (SAR) pre-positioning, field medics, and reception center triage. 

Critical maritime and overland transit corridors suffer from severe humanitarian information asymmetry: weather deterioration and flash flood conditions often trigger mass distress events hours before official dispatch channels can mobilize. 

Refugee Radar solves this by autonomously aggregating zero-auth public telemetry every 30 minutes, running corridor-specific deterministic physics and early-warning algorithms, and rendering real-time operational situation reports (SITREP).

> ⚠️ **Ethical Disclaimer & "Do No Harm" Principle:**  
> This platform is engineered strictly for **civil humanitarian responders, maritime SAR vessels, and medical triage teams**. It is NOT a navigation, crossing-planning, or border evasion tool. It enforces zero user tracking, operates read-only, and collects no personally identifiable information (PII).

---

## 2. Key Capabilities & Mathematical Models

### Corridor A: Central Mediterranean (Tunisia / Libya → Lampedusa)
* **"Trap Window" Detection:** Identifies deceptive calm coastal departures followed by rapid mid-strait squall or sea-state deterioration within 12–24h ($H_s \ge 1.4\text{ m}$ or gusts $\ge 38\text{ km/h}$).
* **Surface Leeway Drift:** Computes real-time leeway drift vectors based on IAMSAR physics:
  $$\text{Drift}_{\text{kts}} = 0.6 + 0.035 \cdot \frac{\overline{W}_{10\text{m}}}{1.852}$$
* **72h Arrival & Capsizing Forward Model:** Evaluates overcrowding risk against Lampedusa Hotspot capacity ($N_{\text{nominal}} = 850, N_{\text{max}} = 1400$).

### Corridor B: Western Balkans Overland (Bihać → Sava / Una Border)
* **Night Windchill & Hypothermia Alerting:** Tracks Plješevica Mountain Pass ($1,200\text{ m}$) apparent temperature minima ($T_{\text{apparent}} < 0^\circ\text{C}$).
* **River Discharge & Swift-Water Warning:** Real-time monitoring of GloFAS Una/Sava river discharge ratio relative to seasonal mean ($Q / Q_{\text{mean}}$) for dangerous river-crossing conditions.

### Corridor C: Eastern Mediterranean / Aegean (Çeşme → Lesbos / Chios)
* **Calm-Run vs. Squall Analysis:** Calculates longest uninterrupted calm-sea windows ($\le 0.75\text{ m}$) against sudden gale spikes ($\ge 35\text{ km/h}$) to forecast arrival surges at Lesbos Mavrovouni CCAC and Chios reception points.

---

## 3. Architecture & Zero-Dependency Pipeline

Refugee Radar is engineered with extreme operational resilience in mind. The backend requires **zero third-party dependencies** (`pip`), running exclusively on the standard library of Python 3:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Public Telemetry APIs (Zero-Auth)                  │
│  Open-Meteo Marine │ Open-Meteo Weather │ GloFAS Flood │ GDELT │ ReliefWeb│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (daemon thread polling every 30 min)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       aegis.py Backend Engine                          │
│  - Deterministic Corridor Evaluation (Algorithms A, B, C)              │
│  - Leeway Drift Vector Calculation                                     │
│  - Atomic write via os.replace -> live_state.json                      │
│  - Embedded HTTP Server (Strictly GET/HEAD read-only)                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Responsive Tactical Frontend                         │
│  - MapLibre GL Interactive Geonavigation (Apple-Studio aesthetic)      │
│  - Dual-Language Support (EN / DE)                                     │
│  - Tactical Interactive Widgets (IAMSAR Drift, Hypothermia, Surge)     │
│  - 1-Click Operational SITREP Dispatch (Signal / Slack markdown)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Quickstart

### Prerequisites
* Python 3.8+ (No `pip install` required!)
* Any modern web browser

### Running Locally
```bash
# Clone the repository
git clone https://github.com/safeaioptimist/refugee-radar.git
cd refugee-radar

# Launch the daemon & HTTP server
python3 aegis.py

# Open your browser at http://127.0.0.1:8080 (or :8081)
```

### Single Execution / CI Test
```bash
python3 aegis.py --once
```

---

## 5. Academic Citation & Metadata

If you reference this software or utilize its models in research or humanitarian operations, please cite using `CITATION.cff`:

```bibtex
@software{safeaioptimist_refugee_radar_2026,
  author = {safeaioptimist},
  title = {Refugee Radar: Route-Adaptive Early Warning & Situational Awareness System for Humanitarian Logistics and Search and Rescue},
  url = {https://github.com/safeaioptimist/refugee-radar},
  version = {1.0.0},
  year = {2026}
}
```

---

## 6. License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see the [LICENSE](LICENSE) file for details.
