# Architekturübersicht: Asynchroner Crawler für defekte Links

## Einleitung
Der Asynchrone Crawler für defekte Links ist auf Effizienz und Skalierbarkeit ausgelegt und nutzt das `asyncio`-Framework von Python für gleichzeitige Operationen. Seine modulare Architektur ermöglicht eine einfache Wartung, Tests und zukünftige Erweiterungen. Dieses Dokument beschreibt die Schlüsselkomponenten und deren Interaktionen.

## Kernkomponenten
Das System besteht hauptsächlich aus den folgenden Modulen:

1.  **`LinkExtractor`**
    *   **Zweck**: Verantwortlich für das Parsen von HTML-Inhalten und das Extrahieren aller auffindbaren Hyperlinks (`<a>`-Tags mit `href`-Attributen).
    *   **Technologie**: Verwendet `BeautifulSoup4` für robustes HTML-Parsing.
    *   **Eingabe**: Roher HTML-Inhalt (String).
    *   **Ausgabe**: Eine Liste von absoluten URLs, die im HTML gefunden wurden.

2.  **`LinkChecker`**
    *   **Zweck**: Führt asynchrone HTTP-Anfragen an eine gegebene URL durch und bestimmt deren Status (z.B. gültig, defekt, Weiterleitung).
    *   **Technologie**: Nutzt `aiohttp` für hochperformante asynchrone HTTP-Client-Operationen.
    *   **Eingabe**: Eine URL (String).
    *   **Ausgabe**: Ein Tupel, das die URL und ihren HTTP-Statuscode (oder einen Fehlerindikator, falls die Anfrage fehlschlägt) enthält.
    *   **Fehlerbehandlung**: Fängt Netzwerkfehler (`aiohttp.ClientError`) ab und gibt einen spezifischen Status zurück (z.B. 0 für Netzwerkprobleme).

3.  **`BrokenLinkReporter`**
    *   **Zweck**: Sammelt und meldet defekte Links. Diese Komponente kann erweitert werden, um verschiedene Ausgabeformate (Konsole, Datei, Datenbank) zu unterstützen.
    *   **Eingabe**: Informationen zu defekten Links (URL, Statuscode, Quellseite).
    *   **Ausgabe**: Formatierter Bericht (derzeit Ausgabe auf der Konsole).
    *   **Zustandsverwaltung**: Speichert eine Liste eindeutiger defekter Links, um doppelte Meldungen zu vermeiden.

4.  **`AsyncWebCrawler`**
    *   **Zweck**: Der Orchestrator des gesamten Crawling-Prozesses. Er verwaltet die Warteschlange der zu besuchenden URLs, verfolgt besuchte URLs und koordiniert zwischen `LinkExtractor`, `LinkChecker` und `BrokenLinkReporter`.
    *   **Technologie**: Basiert auf `asyncio` für die Aufgabenverwaltung und `asyncio.Semaphore` zur Steuerung der Parallelität.
    *   **Schlüsselmethoden**:
        *   `__init__`: Initialisiert den Crawler mit einer Start-URL, maximaler Tiefe und Parallelitätsgrenze.
        *   `_fetch_and_parse_page`: Holt eine Seite, extrahiert Links und gibt sowohl den Seiteninhalt als auch die extrahierten Links zurück.
        *   `_check_link`: Überprüft einen einzelnen Link asynchron mit dem `LinkChecker`.
        *   `_crawl_page`: Die rekursive Kernfunktion, die eine Seite abruft, deren Links extrahiert, neue Links zur Warteschlange hinzufügt und Prüfungen für alle extrahierten Links plant.
        *   `run`: Der Haupteinstiegspunkt, um den Crawling-Prozess zu starten. Er initialisiert die Warteschlange und verwaltet die Worker-Aufgaben.
    *   **Zustandsverwaltung**: Verwendet ein `set` für `visited_urls`, um redundante Verarbeitung und Endlosschleifen zu verhindern, und eine `asyncio.Queue` zur Verwaltung der zu crawllenden URLs.

## Asynchrone Natur
Die Leistung des Projekts hängt stark von `asyncio` und `aiohttp` ab:
-   **`asyncio.gather`**: Wird verwendet, um mehrere `LinkChecker`-Aufgaben gleichzeitig für alle auf einer Seite gefundenen Links auszuführen.
-   **`asyncio.Semaphore`**: Begrenzt die Anzahl der gleichzeitigen HTTP-Anfragen, um eine Überlastung des Zielservers zu vermeiden und die Ressourcennutzung zu steuern.
-   **`asyncio.Queue`**: Erleichtert ein Produzent-Konsument-Muster, bei dem `_crawl_page`-Funktionen neue URLs produzieren und Worker-Aufgaben diese konsumieren.

## Datenfluss und Interaktion
1.  Die Methode `AsyncWebCrawler.run()` initialisiert den Crawling-Prozess, indem die `start_url` zu einer `asyncio.Queue` hinzugefügt wird.
2.  Mehrere Worker-Aufgaben (begrenzt durch `concurrency_limit`) werden gestartet, die kontinuierlich URLs aus der Warteschlange ziehen.
3.  Für jede URL ruft eine Worker-Aufgabe `_crawl_page` auf:
    a.  Sie ruft den HTML-Inhalt mit `aiohttp` ab.
    b.  `LinkExtractor` parst das HTML, um neue Links zu finden.
    c.  Jeder extrahierte Link wird dann vom `LinkChecker` gleichzeitig überprüft.
    d.  Wenn ein Link defekt ist, zeichnet `BrokenLinkReporter` dies auf.
    e.  Neue, unbesuchte und im Geltungsbereich liegende Links werden zur weiteren Überprüfung wieder der `asyncio.Queue` hinzugefügt.
4.  Der Prozess wird fortgesetzt, bis die Warteschlange leer ist und alle Aufgaben abgeschlossen sind, wobei die `max_depth` und `concurrency_limit` eingehalten werden.

## Fehlerbehandlung
-   **HTTP-Fehler**: `LinkChecker` gibt den tatsächlichen HTTP-Statuscode zurück, wodurch `AsyncWebCrawler` 4xx/5xx-Fehler als defekte Links identifizieren kann.
-   **Netzwerkfehler**: `aiohttp.ClientError` wird während des Abrufs abgefangen, und diese Links werden mit einem speziellen Fehlerstatus gemeldet.
-   **Timeout**: Die `aiohttp`-Client-Session kann mit Timeouts konfiguriert werden, um zu verhindern, dass Aufgaben auf unbestimmte Zeit hängen bleiben.

## Erweiterbarkeit
-   **Berichterstattung**: Der `BrokenLinkReporter` kann leicht erweitert werden, um verschiedene Ausgabeformate (z.B. JSON, CSV, Datenbank) zu unterstützen.
-   **Link-Filterung**: Zusätzliche Logik kann zu `LinkExtractor` oder `AsyncWebCrawler` hinzugefügt werden, um Links basierend auf Domains, Dateitypen oder spezifischen Mustern zu filtern.
-   **Authentifizierung**: `aiohttp`-Client-Sessions können mit Authentifizierungsheadern für das Crawling geschützter Websites konfiguriert werden.

## Überlegungen zur Skalierbarkeit
-   **Parallelität**: Das `asyncio.Semaphore` gewährleistet eine kontrollierte Parallelität und verhindert Ressourcenerschöpfung.
-   **Speichernutzung**: Das Verfolgen von `visited_urls` mit einem `set` ist effizient. Für extrem große Crawls könnte eine persistente Speicherung (z.B. Redis) für besuchte URLs und Warteschlangen in Betracht gezogen werden.
-   **Verteiltes Crawling**: Obwohl derzeit Single-Node, macht das modulare Design es anpassbar für verteilte Setups (z.B. unter Verwendung einer gemeinsamen Warteschlange wie RabbitMQ oder Kafka).

Diese Architektur bietet eine solide Grundlage für ein robustes und effizientes System zur Erkennung defekter Links, bereit für den Einsatz auf Unternehmensebene.