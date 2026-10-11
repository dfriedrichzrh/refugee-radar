import os

HERE = "/home/dirkinjo/aegis-radar"
INDEX_PATH = os.path.join(HERE, "index.html")
PREVIEW_PATH = os.path.join(HERE, "preview.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    orig = f.read()

# Extract the entire proven JavaScript engine from index.html
script_start = orig.find("<script>")
script_content = orig[script_start:]

apple_pro_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Refugee Radar // Apple Pro Command Center</title>
  
  <!-- MapLibre GL CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" />
  <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
  
  <style>
    /* ==========================================================================
       APPLE SENIOR DESIGNER // PRO COMMAND CENTER DESIGN SYSTEM
       macOS Sequoia / VisionOS Light Precision Theme (Zero-Scroll Viewport)
       ========================================================================== */
    :root {
      --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
      --font-mono: "SF Mono", Menlo, Monaco, ui-monospace, monospace;
      
      /* Apple Pro System Palette */
      --apple-blue: #007AFF;
      --apple-red: #FF3B30;
      --apple-orange: #FF9500;
      --apple-green: #34C759;
      --apple-purple: #AF52DE;
      
      --accent-blue: #007AFF;
      --accent-blue-light: rgba(0, 122, 255, 0.08);
      --accent-red: #FF3B30;
      --accent-red-light: rgba(255, 59, 48, 0.08);
      --accent-amber: #FF9500;
      --accent-amber-light: rgba(255, 149, 0, 0.08);
      --accent-green: #34C759;
      --accent-green-light: rgba(52, 199, 89, 0.08);
      
      /* Surface & Materials */
      --bg-studio: #F1F5F9;
      --bg-canvas: #F8FAFC;
      --surface-glass: rgba(255, 255, 255, 0.88);
      --surface-glass-heavy: rgba(255, 255, 255, 0.96);
      --border-hairline: rgba(15, 23, 42, 0.08);
      --border-subtle: rgba(15, 23, 42, 0.14);
      
      --text-main: #0F172A;
      --text-muted: #64748B;
      --text-secondary: #475569;
      
      --shadow-apple-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
      --shadow-apple-md: 0 4px 14px rgba(15, 23, 42, 0.06);
      --shadow-apple-lg: 0 12px 32px -4px rgba(15, 23, 42, 0.12);
      
      --radius-xs: 4px;
      --radius-sm: 6px;
      --radius-md: 9px;
      --radius-lg: 12px;
      --radius-pill: 9999px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    html, body {
      width: 100%;
      height: 100vh;
      max-height: 100vh;
      overflow: hidden;
      font-family: var(--font-sans);
      background: var(--bg-studio);
      color: var(--text-main);
      display: flex;
      flex-direction: column;
    }

    /* --------------------------------------------------------------------------
       TOP NAVIGATION BAR (Ultra-sleek 46px macOS Header)
       -------------------------------------------------------------------------- */
    .apple-nav {
      height: 46px;
      min-height: 46px;
      background: var(--surface-glass);
      backdrop-filter: blur(24px) saturate(190%);
      border-bottom: 1px solid var(--border-hairline);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1rem;
      z-index: 100;
    }

    .nav-brand {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .brand-logo {
      font-weight: 700;
      font-size: 0.95rem;
      letter-spacing: -0.02em;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .brand-badge {
      font-size: 0.625rem;
      font-weight: 700;
      font-family: var(--font-mono);
      letter-spacing: 0.04em;
      background: rgba(0, 122, 255, 0.1);
      color: var(--apple-blue);
      border: 1px solid rgba(0, 122, 255, 0.2);
      padding: 0.15rem 0.4rem;
      border-radius: var(--radius-xs);
      text-transform: uppercase;
    }

    .live-pulse {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 600;
      color: var(--apple-green);
      background: rgba(52, 199, 89, 0.08);
      border: 1px solid rgba(52, 199, 89, 0.2);
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-pill);
    }

    .pulse-dot {
      width: 6px;
      height: 6px;
      background: var(--apple-green);
      border-radius: 50%;
      box-shadow: 0 0 6px rgba(52, 199, 89, 0.6);
      animation: pulseGlow 2s infinite ease-in-out;
    }

    @keyframes pulseGlow {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.7; }
    }

    /* Apple macOS Segmented Sector Switcher in Navigation */
    .corridor-bar {
      display: flex;
      align-items: center;
      background: rgba(15, 23, 42, 0.05);
      padding: 2px;
      border-radius: var(--radius-md);
      border: 1px solid rgba(15, 23, 42, 0.06);
    }

    .corridor-tab {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.25rem 0.65rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      white-space: nowrap;
    }

    .corridor-tab:hover {
      color: var(--text-main);
    }

    .corridor-tab.active {
      background: #FFFFFF;
      color: var(--text-main);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04);
    }

    .corridor-tab .c-risk {
      font-size: 0.65rem;
      font-family: var(--font-mono);
      font-weight: 700;
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
    }

    .corridor-tab .c-sub {
      display: none; /* Hide heavy subtitle in sleek segmented control */
    }

    /* Nav Action Buttons */
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 0.45rem;
    }

    .btn-apple {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.28rem 0.65rem;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
      background: #FFFFFF;
      color: var(--text-main);
      box-shadow: var(--shadow-apple-sm);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-apple:hover {
      background: #F8FAFC;
      border-color: var(--border-subtle);
      box-shadow: var(--shadow-apple-md);
      transform: translateY(-0.5px);
    }

    .btn-apple-primary {
      background: var(--apple-blue);
      color: #FFFFFF;
      border-color: var(--apple-blue);
      box-shadow: 0 1px 3px rgba(0, 122, 255, 0.3);
    }

    .btn-apple-primary:hover {
      background: #0066D6;
      border-color: #0066D6;
      color: #FFFFFF;
      box-shadow: 0 3px 8px rgba(0, 122, 255, 0.4);
    }

    /* --------------------------------------------------------------------------
       COMMAND WORKSPACE (Zero-Scroll 2-Column Split: 62% Map | 38% Telemetry)
       -------------------------------------------------------------------------- */
    .workspace-grid {
      flex: 1;
      height: calc(100vh - 46px - 48px);
      display: grid;
      grid-template-columns: 1fr 430px;
      overflow: hidden;
      position: relative;
    }

    /* LEFT PANE: Full-Bleed Map Canvas with Floating HUDs */
    .map-canvas-pane {
      position: relative;
      width: 100%;
      height: 100%;
      background: #E2E8F0;
    }

    #tactical-map {
      width: 100%;
      height: 100%;
    }

    /* Floating Glass HUD: Sector Status */
    .hud-sector-card {
      position: absolute;
      top: 12px;
      left: 12px;
      background: var(--surface-glass);
      backdrop-filter: blur(20px) saturate(190%);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.55rem 0.85rem;
      box-shadow: var(--shadow-apple-md);
      z-index: 10;
      max-width: 320px;
    }

    .hud-title {
      font-size: 0.65rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }

    .hud-corridor-row {
      display: flex;
      align-items: baseline;
      gap: 0.4rem;
      margin-top: 0.1rem;
    }

    .hud-name {
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--text-main);
      letter-spacing: -0.01em;
    }

    .hud-risk {
      font-size: 0.825rem;
      font-family: var(--font-mono);
      font-weight: 700;
    }

    .hud-status {
      font-size: 0.7rem;
      color: var(--text-secondary);
      margin-top: 0.15rem;
      line-height: 1.35;
    }

    /* Floating Glass HUD: Layer Controls & Swatches */
    .hud-layers {
      position: absolute;
      bottom: 12px;
      left: 12px;
      background: var(--surface-glass);
      backdrop-filter: blur(20px) saturate(190%);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.4rem 0.6rem;
      box-shadow: var(--shadow-apple-md);
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .map-toggles {
      display: flex;
      gap: 0.3rem;
    }

    .toggle-pill {
      font-size: 0.675rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-xs);
      border: 1px solid var(--border-hairline);
      background: #FFFFFF;
      color: var(--text-secondary);
      cursor: pointer;
      transition: all 0.12s ease;
    }

    .toggle-pill.active {
      background: var(--apple-blue);
      color: #FFFFFF;
      border-color: var(--apple-blue);
    }

    .map-legend {
      display: flex;
      gap: 0.5rem;
      font-size: 0.65rem;
      color: var(--text-muted);
      padding-top: 0.25rem;
      border-top: 1px solid rgba(0, 0, 0, 0.04);
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .legend-swatch {
      width: 7px;
      height: 7px;
      border-radius: 2px;
    }

    /* Mayday Leeway Drift Tool Drawer */
    .datum-control-bar {
      position: absolute;
      top: 12px;
      right: 3.75rem; /* Safe offset avoiding MapLibre + / - zoom buttons */
      z-index: 10;
    }

    .btn-datum-toggle {
      background: var(--surface-glass);
      backdrop-filter: blur(20px) saturate(190%);
      border: 1px solid rgba(255, 59, 48, 0.25);
      color: var(--apple-red);
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.35rem 0.65rem;
      border-radius: var(--radius-sm);
      box-shadow: var(--shadow-apple-sm);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: all 0.15s ease;
    }
    .btn-datum-toggle:hover {
      background: #FFFFFF;
      box-shadow: var(--shadow-apple-md);
    }

    .datum-card {
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.75rem;
      box-shadow: var(--shadow-apple-lg);
      width: 280px;
      display: none;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 0.4rem;
    }
    .datum-card.active { display: flex; }

    /* RIGHT PANE: Tactical Telemetry Inspector */
    .telemetry-pane {
      background: #FFFFFF;
      border-left: 1px solid var(--border-hairline);
      height: 100%;
      overflow-y: auto;
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    /* 4 Compact Telemetry Metric Cards */
    .metrics-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.45rem;
    }

    .metric-card {
      background: var(--bg-canvas);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.65rem;
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
      transition: all 0.12s ease;
    }
    .metric-card:hover {
      border-color: var(--border-subtle);
      background: #FFFFFF;
      box-shadow: var(--shadow-apple-sm);
    }

    .metric-label {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .metric-value {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      display: flex;
      align-items: baseline;
      gap: 0.2rem;
    }

    .metric-unit {
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-muted);
    }

    .metric-sub {
      font-size: 0.675rem;
      color: var(--text-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .metric-bench {
      font-size: 0.625rem;
      color: var(--text-muted);
      margin-top: 0.1rem;
      line-height: 1.25;
    }

    /* 72h Forecast Chart Card */
    .chart-card {
      background: #FFFFFF;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.65rem 0.75rem;
      box-shadow: var(--shadow-apple-sm);
    }

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 0.4rem;
    }

    .chart-title-wrap {
      display: flex;
      flex-direction: column;
    }

    .card-title {
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: var(--text-main);
    }

    .card-subtitle {
      font-size: 0.675rem;
      color: var(--text-muted);
      margin-top: 0.05rem;
    }

    /* Clean Legend Pills Bar (Replacing Old Clunky Black Box) */
    .chart-legend-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.35rem;
      padding: 0.3rem 0.5rem;
      margin-bottom: 0.4rem;
      background: var(--bg-canvas);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-xs);
      font-size: 0.685rem;
      font-family: var(--font-mono);
    }

    .legend-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.12rem 0.4rem;
      border-radius: 4px;
      font-weight: 500;
      background: #FFFFFF;
      border: 1px solid var(--border-hairline);
      color: var(--text-secondary);
    }

    .legend-pill .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .legend-pill .val {
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }

    .chart-container {
      position: relative;
      width: 100%;
      height: 135px;
    }

    .chart-svg {
      width: 100%;
      height: 100%;
      overflow: visible;
    }

    .chart-cursor {
      stroke: var(--apple-blue);
      stroke-width: 1.5;
      stroke-dasharray: 3 3;
      pointer-events: none;
    }

    /* Reception Capacity Card */
    .capacity-card {
      background: #FFFFFF;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.65rem 0.75rem;
      box-shadow: var(--shadow-apple-sm);
    }

    .hotspot-banner {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      margin-top: 0.35rem;
    }

    .hotspot-track {
      width: 100%;
      height: 7px;
      background: #E2E8F0;
      border-radius: var(--radius-pill);
      overflow: hidden;
    }

    .hotspot-fill {
      height: 100%;
      background: var(--apple-blue);
      border-radius: var(--radius-pill);
      transition: width 0.3s ease;
    }

    /* Autonomous Sensor Fusion Feed */
    .agent-card {
      background: var(--bg-canvas);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 0.65rem 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .feed-item {
      display: flex;
      gap: 0.4rem;
      font-size: 0.7rem;
      line-height: 1.35;
      padding: 0.3rem 0;
      border-bottom: 1px solid rgba(0, 0, 0, 0.04);
    }
    .feed-item:last-child { border-bottom: none; }

    .feed-badge {
      font-size: 0.6rem;
      font-family: var(--font-mono);
      font-weight: 700;
      background: #E2E8F0;
      color: var(--text-secondary);
      padding: 0.1rem 0.35rem;
      border-radius: 3px;
      height: fit-content;
    }

    /* --------------------------------------------------------------------------
       BOTTOM SCRUB DOCK (48px macOS Precision Playback Bar)
       -------------------------------------------------------------------------- */
    .apple-dock {
      height: 48px;
      min-height: 48px;
      background: var(--surface-glass-heavy);
      backdrop-filter: blur(24px) saturate(190%);
      border-top: 1px solid var(--border-hairline);
      display: flex;
      align-items: center;
      padding: 0 1rem;
      gap: 0.85rem;
      z-index: 100;
    }

    .btn-play-pause {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      border: 1px solid var(--border-hairline);
      background: var(--text-main);
      color: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      cursor: pointer;
      box-shadow: var(--shadow-apple-sm);
      transition: all 0.15s ease;
      flex-shrink: 0;
    }
    .btn-play-pause:hover {
      transform: scale(1.05);
      background: var(--apple-blue);
      border-color: var(--apple-blue);
    }

    .dock-scrubber-wrap {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }

    .scrubber-slider {
      flex: 1;
      -webkit-appearance: none;
      height: 5px;
      border-radius: 3px;
      background: #CBD5E1;
      outline: none;
      cursor: pointer;
      transition: background 0.15s;
    }
    .scrubber-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 15px;
      height: 15px;
      border-radius: 50%;
      background: var(--apple-blue);
      border: 2px solid #FFFFFF;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
      cursor: pointer;
      transition: transform 0.1s ease;
    }
    .scrubber-slider::-webkit-slider-thumb:hover {
      transform: scale(1.2);
    }

    .dock-time-pill {
      font-size: 0.725rem;
      font-family: var(--font-mono);
      font-weight: 600;
      color: var(--text-main);
      background: #FFFFFF;
      border: 1px solid var(--border-hairline);
      padding: 0.25rem 0.6rem;
      border-radius: var(--radius-sm);
      box-shadow: var(--shadow-apple-sm);
      white-space: nowrap;
    }

    .dock-anchors {
      display: flex;
      gap: 0.25rem;
    }

    .dock-anchor-btn {
      font-size: 0.65rem;
      font-family: var(--font-mono);
      font-weight: 600;
      color: var(--text-muted);
      background: transparent;
      border: 1px solid transparent;
      padding: 0.18rem 0.4rem;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.12s ease;
    }
    .dock-anchor-btn:hover {
      background: rgba(15, 23, 42, 0.06);
      color: var(--text-main);
    }

    /* Modals & Tour Styling */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.45);
      backdrop-filter: blur(8px);
      z-index: 2000;
      display: none;
      align-items: center;
      justify-content: center;
    }
    .modal-backdrop.active { display: flex; }

    .modal-window {
      background: #FFFFFF;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-apple-lg);
      width: 90%;
      max-width: 620px;
      max-height: 85vh;
      overflow-y: auto;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    /* Guided Tour Banner */
    .tour-banner {
      position: fixed;
      top: 56px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-apple-lg);
      padding: 0.85rem 1.15rem;
      z-index: 2000;
      width: 90%;
      max-width: 540px;
      display: none;
      flex-direction: column;
      gap: 0.45rem;
    }
    .tour-banner.active { display: flex; }
    .tour-highlight {
      position: relative;
      z-index: 1001 !important;
      box-shadow: 0 0 0 4px var(--apple-blue), 0 12px 30px rgba(0, 122, 255, 0.25) !important;
    }
  </style>
</head>
<body>

  <!-- TOP APPLE NAV -->
  <header class="apple-nav">
    <div class="nav-brand">
      <div class="brand-logo">
        <span style="color:var(--apple-blue); font-size:1.1rem;">⚓</span>
        <span>Refugee Radar</span>
      </div>
      <span class="brand-badge">PRO COMMAND</span>
      <div class="live-pulse">
        <div class="pulse-dot"></div>
        <span id="lbl-live-badge">LIVE AUTONOMOUS PATROL</span>
      </div>
    </div>

    <!-- macOS Segmented Corridor Tabs -->
    <div class="corridor-bar" id="corridor-tabs">
      <!-- Rendered by JS -->
    </div>

    <div class="nav-actions">
      <button class="btn-apple btn-apple-primary" onclick="startGuidedTour()">
        <span>▶</span> <span>30s Tour</span>
      </button>
      <button class="btn-apple" onclick="openSitrepModal()" id="lbl-report-bar">
        <span>📋</span> <span>SITREP</span>
      </button>
      <button class="btn-apple" onclick="toggleLanguage()" id="btn-lang" style="font-family:var(--font-mono);">
        DE
      </button>
      <button class="btn-apple" onclick="openFaqModal()" id="lbl-faq">
        FAQ
      </button>
    </div>
  </header>

  <!-- MAIN WORKSPACE: MAP (62%) + TELEMETRY INSPECTOR (38%) -->
  <main class="workspace-grid">
    
    <!-- LEFT: MAP CANVAS -->
    <div class="map-canvas-pane">
      <div id="tactical-map"></div>

      <!-- Floating HUD: Selected Sector Card -->
      <div class="hud-sector-card">
        <div class="hud-title" id="lbl-map-focus">Sector Radar Status</div>
        <div class="hud-corridor-row">
          <span class="hud-name" id="map-corridor-name">Pan-Med & Balkan Radar</span>
          <span class="hud-risk" id="map-corridor-risk" style="color:var(--apple-amber);">(Ø 58%)</span>
        </div>
        <div class="hud-status" id="map-corridor-status">
          3 aktive Überwachungssektoren · Brennpunkt: Ägäis (89%)
        </div>
      </div>

      <!-- Floating HUD: Mayday Leeway Drift Tool -->
      <div class="datum-control-bar" id="datum-control-bar">
        <button class="btn-datum-toggle" id="btn-toggle-datum" onclick="toggleDatumCard()">
          🧭 <span id="lbl-datum-btn">Mayday Drift</span>
        </button>

        <div class="datum-card" id="datum-panel">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.75rem; font-weight:700; color:var(--text-main);" id="lbl-datum-card-title">🚨 Mayday Drift Calculator</span>
            <span style="cursor:pointer; color:var(--text-muted); font-size:1.1rem;" onclick="toggleDatumCard()">&times;</span>
          </div>

          <div>
            <label style="font-size:0.65rem; color:var(--text-muted); font-weight:600;" id="lbl-vessel-type">Craft Type (Leeway)</label>
            <select class="select-ctrl" id="datum-vessel-type" style="width:100%; height:26px; font-size:0.725rem; border-radius:4px; border:1px solid var(--border-hairline); margin-top:2px;" onchange="updateDatumCalculation()">
              <option value="dinghy">Rubber Dinghy / Schlauchboot (2.8% wind)</option>
              <option value="wood">Overcrowded Wooden Boat (1.4% wind)</option>
              <option value="metal">Iron Boat / Metallkahn (1.0% wind)</option>
              <option value="piw">Person in Water / PIW (0.8% wind)</option>
            </select>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px;">
            <input type="number" step="0.01" id="datum-lon" style="padding:4px; font-size:0.725rem; border-radius:4px; border:1px solid var(--border-hairline);" placeholder="Lon" value="12.2" onchange="updateDatumFromInputs()">
            <input type="number" step="0.01" id="datum-lat" style="padding:4px; font-size:0.725rem; border-radius:4px; border:1px solid var(--border-hairline);" placeholder="Lat" value="35.1" onchange="updateDatumFromInputs()">
          </div>

          <div style="background:var(--bg-canvas); padding:0.4rem; border-radius:4px; font-size:0.7rem; font-family:var(--font-mono);">
            <div>Speed: <span id="val-leeway-speed" style="font-weight:700;">1.2 kts</span> (<span id="val-leeway-brg">145°</span>)</div>
            <div>Area: <span id="val-leeway-area" style="font-weight:700;">34.8 NM²</span></div>
          </div>

          <button class="btn-apple btn-apple-primary" style="height:26px; font-size:0.7rem; justify-content:center;" onclick="activateMapCrosshair()">
            🎯 <span id="lbl-pick-map">Click Map to Place</span>
          </button>
        </div>
      </div>

      <!-- Floating HUD: Layer Pills & Color Swatches -->
      <div class="hud-layers">
        <div class="map-toggles">
          <button class="toggle-pill active" id="toggle-waves" onclick="toggleLayer('waves')">🌊 Sea</button>
          <button class="toggle-pill active" id="toggle-wind" onclick="toggleLayer('wind')">💨 Wind</button>
          <button class="toggle-pill active" id="toggle-sar" onclick="toggleLayer('sar')">🎯 SAR</button>
          <button class="toggle-pill active" id="toggle-hotspots" onclick="toggleLayer('hotspots')">🏛️ Camps</button>
        </div>
        <div class="map-legend">
          <div class="legend-item"><div class="legend-swatch" style="background:#34C759;"></div> <span id="leg-calm">Calm (&lt;0.8m)</span></div>
          <div class="legend-item"><div class="legend-swatch" style="background:#FF9500;"></div> <span id="leg-rough">Capsize (&gt;1.5m)</span></div>
          <div class="legend-item"><div class="legend-swatch" style="background:#FF3B30;"></div> <span id="leg-severe">Severe (&gt;2.2m)</span></div>
        </div>
      </div>
    </div>

    <!-- RIGHT: TACTICAL TELEMETRY INSPECTOR -->
    <div class="telemetry-pane">
      
      <!-- 4 Compact Telemetry Metric Chips -->
      <div class="metrics-row">
        <div class="metric-card">
          <span class="metric-label" id="lbl-m-wave">Wave Height</span>
          <span class="metric-value"><span id="val-wave">1.26</span> <span class="metric-unit" id="unit-wave">m</span></span>
          <span class="metric-sub" id="sub-wave">Significant sea</span>
          <span class="metric-bench" id="bench-wave">Threshold: 1.5m</span>
        </div>
        <div class="metric-card">
          <span class="metric-label" id="lbl-m-wind">Peak Gusts</span>
          <span class="metric-value"><span id="val-gust">57</span> <span class="metric-unit" id="unit-gust">km/h</span></span>
          <span class="metric-sub" id="sub-gust">Offshore drift</span>
          <span class="metric-bench" id="bench-gust">Normal: &lt;25 km/h</span>
        </div>
        <div class="metric-card">
          <span class="metric-label" id="lbl-m-arrivals">Arrival Rate</span>
          <span class="metric-value"><span id="val-arrivals">2.1</span> <span class="metric-unit" id="unit-arrivals">ppl/h</span></span>
          <span class="metric-sub" id="sub-arrivals">Avg rate</span>
          <span class="metric-bench" id="bench-arrivals">UNHCR baseline</span>
        </div>
        <div class="metric-card">
          <span class="metric-label" id="lbl-m-hotspot">Capacity</span>
          <span class="metric-value"><span id="val-hotspot-occ">88</span> <span class="metric-unit">%</span></span>
          <span class="metric-sub" id="sub-hotspot-occ">Lampedusa</span>
          <span class="metric-bench" id="bench-hotspot">Puffer headroom</span>
        </div>
      </div>

      <!-- 72h Multi-Sector Horizon Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title-wrap">
            <span class="card-title" id="lbl-chart-title">📈 72h Multi-Sector Hazard Comparison</span>
            <span class="card-subtitle" id="lbl-chart-sub">Simultaneous 3-corridor dynamics</span>
          </div>
        </div>

        <!-- Legend Pills directly above chart -->
        <div id="chart-legend-bar" class="chart-legend-bar"></div>

        <div class="chart-container" id="timeline-chart-wrap">
          <svg class="chart-svg" id="timeline-chart" preserveAspectRatio="none"></svg>
        </div>
      </div>

      <!-- Reception Capacity Gauge -->
      <div class="capacity-card">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <span class="card-title" style="font-size:0.75rem;" id="lbl-capacity-title">🏛️ Reception Headroom</span>
          <span id="hotspot-percent-label" style="font-family:var(--font-mono); font-weight:700; font-size:0.75rem;">88%</span>
        </div>
        <div class="hotspot-banner">
          <div class="hotspot-track">
            <div class="hotspot-fill" id="hotspot-fill" style="width:88%;"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:var(--text-muted); font-family:var(--font-mono);">
            <span id="hotspot-name-label">Hotspot Facility</span>
            <span id="hotspot-counts-label">680 / 850 Beds</span>
          </div>
        </div>
      </div>

      <!-- Autonomous Agent Telemetry Stream -->
      <div class="agent-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:0.725rem; font-weight:700; color:var(--text-main);" id="lbl-agent-title">🤖 Autonomous Sensor Fusion</span>
          <span style="font-size:0.625rem; font-family:var(--font-mono); color:var(--apple-green); font-weight:600;">CYCLE 30M ACTIVE</span>
        </div>
        <div id="agent-feed-list" style="display:flex; flex-direction:column; gap:0.25rem;">
          <!-- Populated by JS -->
        </div>
      </div>

    </div>
  </main>

  <!-- BOTTOM DOCK: 72H PLAYBACK CONTROLS (macOS Timeline Scrub Bar) -->
  <footer class="apple-dock">
    <button class="btn-play-pause" id="sim-toggle-btn" onclick="toggleSimulation()">▶</button>
    
    <div class="dock-scrubber-wrap">
      <input type="range" min="0" max="71" value="0" class="scrubber-slider" id="time-scrubber" oninput="onScrubChange(this.value)" />
    </div>

    <div class="dock-time-pill" id="sim-time-label">
      Cursor: T+0h · 11 Oct 08:00 UTC
    </div>

    <div class="dock-anchors">
      <button class="dock-anchor-btn" onclick="document.getElementById('time-scrubber').value=0; onScrubChange(0);">T+0h</button>
      <button class="dock-anchor-btn" onclick="document.getElementById('time-scrubber').value=24; onScrubChange(24);">T+24h</button>
      <button class="dock-anchor-btn" onclick="document.getElementById('time-scrubber').value=48; onScrubChange(48);">T+48h</button>
      <button class="dock-anchor-btn" onclick="document.getElementById('time-scrubber').value=71; onScrubChange(71);">T+72h</button>
    </div>
  </footer>

  <!-- MODALS: SITREP & FAQ -->
  <div class="modal-backdrop" id="sitrep-modal">
    <div class="modal-window">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="font-size:1rem; font-weight:700;" id="sitrep-modal-title">📋 Humanitarian SITREP Dispatch</h3>
        <span style="cursor:pointer; font-size:1.2rem; color:var(--text-muted);" onclick="closeSitrepModal()">&times;</span>
      </div>
      <div id="sitrep-modal-body">
        <div id="sitrep-body"></div>
      </div>
      <textarea id="sitrep-text" style="position:absolute; left:-9999px;"></textarea>
      <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
        <button class="btn-apple" onclick="closeSitrepModal()">Close</button>
        <button class="btn-apple btn-apple-primary" id="btn-copy-sitrep" onclick="copySitrep()">Copy for Signal / Email</button>
      </div>
    </div>
  </div>

  <div class="modal-backdrop" id="faq-modal">
    <div class="modal-window">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="font-size:1rem; font-weight:700;" id="faq-modal-title">About Refugee Radar</h3>
        <span style="cursor:pointer; font-size:1.2rem; color:var(--text-muted);" onclick="closeFaqModal()">&times;</span>
      </div>
      <div id="faq-modal-body" style="font-size:0.825rem; line-height:1.6; color:var(--text-secondary);"></div>
      <div style="display:flex; justify-content:flex-end;">
        <button class="btn-apple" onclick="closeFaqModal()">Close</button>
      </div>
    </div>
  </div>

  <!-- GUIDED TOUR BANNER -->
  <div class="tour-banner" id="tour-banner">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <span class="brand-badge" id="tour-step-badge">STEP 1 OF 5</span>
      <span style="cursor:pointer; color:var(--text-muted); font-size:1.1rem;" onclick="stopGuidedTour()">&times;</span>
    </div>
    <div style="font-size:0.95rem; font-weight:700; color:var(--text-main);" id="tour-title">Tour Title</div>
    <div style="font-size:0.8rem; color:var(--text-secondary); line-height:1.45;" id="tour-desc">Tour description...</div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem;">
      <div style="display:flex; gap:0.3rem;" id="tour-dots"></div>
      <button class="btn-apple btn-apple-primary" style="padding:0.2rem 0.6rem; font-size:0.75rem;" onclick="nextTourStep()">Next →</button>
    </div>
  </div>
"""

full_content = apple_pro_html + "\n" + script_content

with open(PREVIEW_PATH, "w", encoding="utf-8") as out:
    out.write(full_content)

print("SUCCESS: Generated", PREVIEW_PATH, "with", len(full_content), "bytes")
