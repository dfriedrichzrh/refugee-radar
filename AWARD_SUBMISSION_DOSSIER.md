# Refugee Radar — Universal Award & Prize Submission Guide
**Author & Lead:** dfriedrichzrh  
**Repository:** https://github.com/dfriedrichzrh/refugee-radar  
**Live System:** https://evening-barbara-displaying-affordable.trycloudflare.com  
**License:** GNU Affero General Public License v3.0 (AGPL-3.0)  

---

## 📌 Schnellübersicht für deine Kalender-Reminder

Wenn dein Kalender dich an einen dieser Termine erinnert, öffne einfach diesen Leitfaden, kopiere die passenden Abschnitte und füge sie in das jeweilige Portal ein:

* **Termin 1 (15. November 2026):** UN WSIS Prizes 2027 $\rightarrow$ Nutze **Teil 2 (English)**
* **Termin 2 (15. Januar 2027):** Prix Ars Electronica $\rightarrow$ Nutze **Teil 2 (English)**
* **Termin 3 (15. Mai 2027):** DINAcon Awards Schweiz $\rightarrow$ Nutze **Teil 1 (Deutsch)**

---

# TEIL 1: Einreichungsdossier DINAcon Awards (Schweiz)
*Zielkategorie: Open Source / Public Impact / Digital Humanity*  
*Veranstalter: CH Open & Forschungsstelle Digitale Nachhaltigkeit, Universität Bern*  
*Portal:* https://dinacon.ch/  
*Sprache: Deutsch*

### 1. Projekt-Kurzbeschreibung (Elevator Pitch für die Schweizer Jury)
> Refugee Radar (AEGIS) ist ein vollständig quelloffenes, ziviles Frühwarn- und Lagezentrum für humanitäre Rettungslogistik, Such- und Rettungseinsätze (SAR) und medizinische Erstaufnahmelager. Das System fusioniert im 30-Minuten-Takt freie, meteorologische und hydrologische Echtzeit-Telemetriedaten (Open-Meteo, Copernicus GloFAS, UN OCHA ReliefWeb, GDELT 2.0) und berechnet physikbasierte Gefahrenkurven für das zentrale Mittelmeer, die Ägäis und den Balkan. Es schließt eine fatale Informationslücke zwischen staatlichen militärischen Lagebildern und zivilen Hilfsorganisationen – mit radikaler Datensparsamkeit und ohne jede Erfassung von Schutzsuchenden.

### 2. Was macht das Projekt digital nachhaltig & herausragend im Sinne von Open Source?
1. **Zero-Dependency-Architektur (Echte Wartungsfreiheit):**  
   Das Backend (`aegis.py`) verzichtet vollständig auf volatile externe Paketökosysteme (`pip`, `npm`) und läuft ausschließlich auf der Standardbibliothek von Python 3. Dadurch ist das System wartungsfrei, extrem ressourcenschonend und gegen Software-Obsoleszenz immun.
2. **Freiheit von proprietären Cloud-Monopolen:**  
   Die Kartennavigation nutzt MapLibre GL anstelle proprietärer Anbieter (wie Google Maps oder Mapbox), wodurch keine Token-Kosten oder Tracking-Mechanismen entstehen.
3. **Konsequente Copyleft-Lizenzierung (GNU AGPLv3):**  
   Die Wahl der AGPL-3.0 garantiert völkerrechtlich und urheberrechtlich, dass das Werk für immer freies Gemeingut bleibt und eine proprietäre oder militärische Instrumentalisierung ausgeschlossen ist.
4. **Wissenschaftliche Transparenz & Zitationsfähigkeit:**  
   Standardisiert über `CITATION.cff` und indexierbar über CERN/Zenodo, macht Refugee Radar zivile Rettungslogistik akademisch nachvollziehbar und reproduzierbar.

### 3. Technische Meisterleistung: Wie funktioniert das System im Detail?
* **Das „Trap Window“-Modell (Sizilien-Kanal):** Identifiziert automatisch die fatale meteorologische Falle: Flache See an der nordafrikanischen Küste ($H_s < 0.65\text{ m}$), gefolgt von schwerem Seegang ($H_s \ge 1.4\text{ m}$, Böen $\ge 38\text{ km/h}$) 12 Stunden später mitten auf hoher See.
* **Mayday-Driftrechner (IAMSAR-Physikmodell):** Berechnet in Echtzeit den Oberflächen-Abtrieb manövrierunfähiger Holz- und Schlauchboote basierend auf den offiziellen Formeln der International Maritime Organization (IMO): $\text{Drift}_{\text{kts}} = 0.6 + 0.035 \cdot (\overline{v}_{\text{wind}} / 1.852)$.
* **Topografische Extremwetter-Warnung (Balkan-Route):** Überwacht den nächtlichen Windchill-Tiefstwert am Plješevica-Bergpass ($1.200\text{ m}$) und vergleicht über Copernicus GloFAS den Abfluss der Una und Sava ($Q / Q_{\text{mean}}$) zur Warnung vor reißenden Flüssen.
* **1-Klick-Lagebericht (SITREP):** Generiert mit einem Tastendruck operative, datengestützte Lageberichte im Markdown-Format, optimiert für Signal- und Slack-Einsatzgruppen vor Ort.

### 4. Gesellschaftlicher Impact & Ethik („Do No Harm“)
* **Schutzschild statt Überwachung:** Während offizielle Grenzschutzagenturen (Frontex) Überwachungstechnologie zur Abschottung einsetzen, stellt Refugee Radar offene Daten in den Dienst des Lebensschutzes.
* **Absoluter Datenschutz (Zero PII):** Das System speichert null Benutzerdaten, setzt keine Cookies, loggt keine IP-Adressen und erfasst keine flüchtenden Menschen. Es operiert als rein lesender Server.

---

# TEIL 2: Submission Dossier for Prix Ars Electronica & UN WSIS
*Category: Digital Humanity / AI & Life Art / E-Science*  
*Portals:* https://ars.electronica.art/prix/de/ & https://www.itu.int/net4/wsis/stocktaking/Prizes/Prizes  
*Language: English*

### 1. Title & Abstract of the Work
* **Title:** Refugee Radar (AEGIS) — Tactical Early-Warning Engine & Civil Humanitarian Radar
* **Short Description:**
> In the Mediterranean and along European overland transit corridors, a deadly information asymmetry costs thousands of lives: asylum seekers are forced onto unseaworthy vessels during deceptive calm weather along the coast, only to encounter fatal squalls in open waters hours later ("The Trap Window"). While state border agencies possess classified military surveillance systems, civil rescue crews, field medics, and reception centers are left blind.
> 
> Refugee Radar is an autonomous, open-source civil situational awareness dashboard that inverts surveillance technology into an instrument of humanitarian protection. Fusing open marine telemetry, river discharge sensors, and humanitarian event streams every 30 minutes, it computes deterministic 72-hour forward arrival risks and real-time IAMSAR leeway drift vectors. Built with zero third-party dependencies in pure Python 3 and MapLibre GL, it enforces radical data privacy: zero tracking, zero cookies, and zero surveillance of individuals.

### 2. Conceptual Background: Why is this "Digital Humanity"?
1. **Democratizing the Humanitarian Horizon:** Breaks the monopoly of classified military situational awareness and provides civil society and volunteer medics with predictive intelligence.
2. **Algorithmic Care instead of Algorithmic Control:** Deploys mathematical models (IAMSAR drift physics, Windchill indices, river discharge ratios) to anticipate human vulnerability rather than monitor individuals.
3. **Radical Minimalism as Resistance:** Rejects bloated cloud monopolies by running purely on the Python 3 standard library with zero external dependencies.

### 3. Links for the Jury
* **Working Public Demo:** https://evening-barbara-displaying-affordable.trycloudflare.com
* **Open Source Codebase:** https://github.com/dfriedrichzrh/refugee-radar
* **Author / Location:** dfriedrichzrh (Zurich, Switzerland)
