# Asynchroner Crawler für defekte Links

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Inhaltsverzeichnis
- [Über dieses Projekt](#über-dieses-projekt)
- [Funktionen](#funktionen)
- [Installation](#installation)
- [Nutzung](#nutzung)
- [Architektur](#architektur)
- [Mitwirken](#mitwirken)
- [Lizenz](#lizenz)

## Über dieses Projekt
Willkommen beim Asynchronen Crawler für defekte Links! Dieses Projekt bietet einen unternehmenstauglichen, hochperformanten asynchronen Web-Crawler, der entwickelt wurde, um defekte Links auf Websites effizient zu erkennen. Durch die Nutzung von Pythons `asyncio` und `aiohttp` kann er Tausende von Links gleichzeitig überprüfen, was ihn ideal für groß angelegte Web-Integritätsprüfungen macht.

## Funktionen
- **Asynchrone Operationen**: Nutzt `asyncio` für die gleichzeitige Link-Überprüfung, wodurch die Crawling-Zeiten drastisch reduziert werden.
- **Skalierbar**: Gebaut, um große Websites und zahlreiche Links ohne Leistungseinbußen zu verarbeiten.
- **Robuste Fehlerbehandlung**: Verwaltet Netzwerkfehler, Timeouts und verschiedene HTTP-Statuscodes elegant.
- **Anpassbare Tiefe**: Konfigurieren Sie, wie tief der Crawler in die Linkstruktur einer Website eindringen soll.
- **Umfassende Berichterstattung**: Erstellt einen klaren Bericht über alle gefundenen defekten Links.
- **Modulares Design**: Einfach zu erweitern und in bestehende Systeme zu integrieren.

## Installation
Um mit dem Asynchronen Crawler für defekte Links zu beginnen, befolgen Sie diese Schritte:

1.  **Klonen Sie das Repository:**
    ```bash
    git clone https://github.com/your-username/async-broken-link-crawler.git
    cd async-broken-link-crawler
    ```

2.  **Erstellen und aktivieren Sie eine virtuelle Umgebung:**
    ```bash
    python -m venv .venv
    # Unter Windows
    .venv\Scripts\activate
    # Unter macOS/Linux
    source .venv/bin/activate
    ```

3.  **Installieren Sie die Abhängigkeiten:**
    ```bash
    pip install -r requirements.txt
    ```

## Nutzung
Nach der Installation können Sie den Crawler über die Befehlszeile ausführen. Das Skript `main.py` dient als Einstiegspunkt.

```bash
python main.py <start_url> [--max-depth <tiefe>] [--concurrency <anzahl_worker>]
```

**Beispiel:** Crawlen Sie `https://example.com` bis zu einer Tiefe von 2, mit 10 gleichzeitigen Anfragen:

```bash
python main.py https://example.com --max-depth 2 --concurrency 10
```

Der Crawler gibt defekte Links direkt in der Konsole aus.

## Architektur
Für ein detailliertes Verständnis des Designs und der internen Funktionsweise des Projekts, lesen Sie bitte unsere Architekturdokumentation:
- [Architecture Overview (English)](./docs/architecture_en.md)
- [Architekturübersicht (Deutsch)](./docs/architecture_de.md)

## Mitwirken
Wir freuen uns über Beiträge aus der Community! Ob es sich um Fehlerberichte, Funktionsanfragen oder Code-Beiträge handelt, Ihre Hilfe ist wertvoll. Bitte beachten Sie unsere Anleitung [CONTRIBUTING.md](./CONTRIBUTING.md) für detaillierte Anweisungen zur Beteiligung.

## Lizenz
Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Details finden Sie in der Datei [LICENSE](./LICENSE).