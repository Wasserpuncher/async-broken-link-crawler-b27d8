import asyncio
import aiohttp
import argparse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Set, List, Tuple, Optional


class LinkExtractor:
    """
    Extrahiert alle Hyperlinks aus dem HTML-Inhalt einer Webseite.
    Extracts all hyperlinks from the HTML content of a webpage.
    """

    def __init__(self, base_url: str):
        """
        Initialisiert den LinkExtractor mit einer Basis-URL.
        Initializes the LinkExtractor with a base URL.

        Args:
            base_url (str): Die Basis-URL, um relative Links in absolute umzuwandeln.
                            The base URL to convert relative links to absolute ones.
        """
        self.base_url = base_url

    def extract_links(self, html_content: str) -> List[str]:
        """
        Parst den HTML-Inhalt und gibt eine Liste aller gefundenen absoluten Links zurück.
        Parses the HTML content and returns a list of all found absolute links.

        Args:
            html_content (str): Der HTML-Inhalt der Webseite.
                                The HTML content of the webpage.

        Returns:
            List[str]: Eine Liste von absoluten URLs.
                       A list of absolute URLs.
        """
        soup = BeautifulSoup(html_content, 'html.parser') # Erstellt ein BeautifulSoup-Objekt zum Parsen des HTML.
                                                      # Creates a BeautifulSoup object to parse the HTML.
        links = []
        for anchor_tag in soup.find_all('a', href=True): # Findet alle <a>-Tags mit einem 'href'-Attribut.
                                                      # Finds all <a> tags with an 'href' attribute.
            href = anchor_tag['href']
            absolute_url = urljoin(self.base_url, href) # Wandelt den Link in eine absolute URL um.
                                                        # Converts the link to an absolute URL.
            links.append(absolute_url)
        return links


class LinkChecker:
    """
    Überprüft den HTTP-Status eines Links asynchron.
    Asynchronously checks the HTTP status of a link.
    """

    def __init__(self, session: aiohttp.ClientSession):
        """
        Initialisiert den LinkChecker mit einer aiohttp ClientSession.
        Initializes the LinkChecker with an aiohttp ClientSession.

        Args:
            session (aiohttp.ClientSession): Die aiohttp ClientSession für HTTP-Anfragen.
                                             The aiohttp ClientSession for HTTP requests.
        """
        self.session = session

    async def check_link(self, url: str) -> Tuple[str, int]:
        """
        Führt eine GET-Anfrage an die gegebene URL durch und gibt den Statuscode zurück.
        Performs a GET request to the given URL and returns its status code.

        Args:
            url (str): Die zu überprüfende URL.
                       The URL to check.

        Returns:
            Tuple[str, int]: Ein Tupel aus der URL und ihrem HTTP-Statuscode (oder 0 bei Netzwerkfehler).
                             A tuple of the URL and its HTTP status code (or 0 for network error).
        """
        try:
            async with self.session.get(url, allow_redirects=True, timeout=10) as response: # Führt eine GET-Anfrage durch und folgt Weiterleitungen.
                                                                                       # Performs a GET request and follows redirects.
                return url, response.status
        except aiohttp.ClientError as e: # Fängt Client-Fehler ab (z.B. DNS-Fehler, Verbindungsprobleme).
                                        # Catches client errors (e.g., DNS errors, connection issues).
            print(f"Fehler beim Überprüfen von {url}: {e}") # Gibt den Fehler aus.
                                                            # Prints the error.
            return url, 0 # Gibt 0 als Statuscode für Fehler zurück.
                          # Returns 0 as status code for errors.
        except asyncio.TimeoutError: # Fängt Timeout-Fehler ab.
                                     # Catches timeout errors.
            print(f"Timeout beim Überprüfen von {url}") # Gibt den Timeout-Fehler aus.
                                                      # Prints the timeout error.
            return url, 0


class BrokenLinkReporter:
    """
    Sammelt und meldet defekte Links.
    Collects and reports broken links.
    """

    def __init__(self):
        """
        Initialisiert den BrokenLinkReporter.
        Initializes the BrokenLinkReporter.
        """
        self.broken_links: Set[Tuple[str, int, str]] = set() # Ein Set, um defekte Links zu speichern (URL, Status, Quellseite).
                                                          # A set to store broken links (URL, status, source page).

    def add_broken_link(self, url: str, status_code: int, source_page: str):
        """
        Fügt einen defekten Link zum Bericht hinzu.
        Adds a broken link to the report.

        Args:
            url (str): Der defekte Link.
                       The broken link.
            status_code (int): Der HTTP-Statuscode des defekten Links.
                               The HTTP status code of the broken link.
            source_page (str): Die Seite, von der der defekte Link gefunden wurde.
                               The page where the broken link was found.
        """
        self.broken_links.add((url, status_code, source_page))

    def generate_report(self):
        """
        Generiert und gibt den Bericht über defekte Links aus.
        Generates and prints the report of broken links.
        """
        if not self.broken_links:
            print("Keine defekten Links gefunden. Wunderbar!") # Keine defekten Links gefunden.
                                                           # No broken links found.
            return

        print("\n--- Bericht über defekte Links ---") # Header für den Bericht.
                                                # Header for the report.
        for url, status, source in sorted(list(self.broken_links)): # Iteriert über die defekten Links und sortiert sie.
                                                                  # Iterates over broken links and sorts them.
            print(f"[DEFEKT] Status: {status} - Link: {url} (gefunden auf: {source})") # Gibt jeden defekten Link aus.
                                                                                 # Prints each broken link.
        print("----------------------------------") # Footer für den Bericht.
                                                # Footer for the report.


class AsyncWebCrawler:
    """
    Ein asynchroner Web-Crawler zur Erkennung defekter Links.
    An asynchronous web crawler for detecting broken links.
    """

    def __init__(self, start_url: str, max_depth: int = 1, concurrency: int = 5):
        """
        Initialisiert den AsyncWebCrawler.
        Initializes the AsyncWebCrawler.

        Args:
            start_url (str): Die Start-URL für den Crawl.
                             The starting URL for the crawl.
            max_depth (int): Die maximale Tiefe, bis zu der der Crawler Links verfolgen soll.
                             The maximum depth the crawler should follow links.
            concurrency (int): Die maximale Anzahl gleichzeitiger HTTP-Anfragen.
                               The maximum number of concurrent HTTP requests.
        """
        self.start_url = self._normalize_url(start_url) # Normalisiert die Start-URL.
                                                      # Normalizes the start URL.
        self.domain = urlparse(self.start_url).netloc # Extrahiert die Domain der Start-URL.
                                                    # Extracts the domain of the start URL.
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.visited_urls: Set[str] = set() # Ein Set, um besuchte URLs zu speichern, um Endlosschleifen zu vermeiden.
                                           # A set to store visited URLs to prevent infinite loops.
        self.to_visit_queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue() # Eine Warteschlange für URLs, die noch besucht werden müssen.
                                                                         # A queue for URLs that still need to be visited.
        self.reporter = BrokenLinkReporter()
        self.semaphore = asyncio.Semaphore(self.concurrency) # Ein Semaphore zur Begrenzung der gleichzeitigen Anfragen.
                                                            # A semaphore to limit concurrent requests.

    def _normalize_url(self, url: str) -> str:
        """
        Normalisiert eine URL, um Duplikate zu vermeiden.
        Normalizes a URL to avoid duplicates.
        """
        parsed_url = urlparse(url)
        # Entfernt Fragmente und stellt sicher, dass ein Schrägstrich am Ende vorhanden ist, wenn es ein Verzeichnis ist.
        # Removes fragments and ensures a trailing slash if it's a directory.
        path = parsed_url.path if parsed_url.path.endswith('/') or '.' in parsed_url.path.split('/')[-1] else parsed_url.path + '/'
        return parsed_url._replace(fragment='', path=path).geturl()

    def _is_same_domain(self, url: str) -> bool:
        """
        Überprüft, ob eine URL zur gleichen Domain wie die Start-URL gehört.
        Checks if a URL belongs to the same domain as the start URL.
        """
        return urlparse(url).netloc == self.domain

    async def _fetch_and_parse_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """
        Holt den HTML-Inhalt einer URL.
        Fetches the HTML content of a URL.
        """
        try:
            async with self.semaphore: # Wartet auf einen Slot im Semaphore.
                                       # Waits for a slot in the semaphore.
                async with session.get(url, allow_redirects=True, timeout=10) as response: # Führt die GET-Anfrage durch.
                                                                                       # Performs the GET request.
                    response.raise_for_status() # Löst eine Ausnahme für 4xx/5xx-Antworten aus.
                                                # Raises an exception for 4xx/5xx responses.
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type: # Überprüft, ob der Inhaltstyp HTML ist.
                                                    # Checks if the content type is HTML.
                        return await response.text()
                    else:
                        print(f"Skipping {url}: Content-Type is not HTML ({content_type})") # Überspringt Nicht-HTML-Inhalte.
                                                                                             # Skips non-HTML content.
                        return None
        except aiohttp.ClientError as e: # Fängt Client-Fehler ab.
                                        # Catches client errors.
            print(f"Fehler beim Abrufen von {url}: {e}") # Gibt den Fehler aus.
                                                        # Prints the error.
            self.reporter.add_broken_link(url, 0, "Crawler Fetch Error") # Meldet den Link als defekt.
                                                                        # Reports the link as broken.
            return None
        except asyncio.TimeoutError: # Fängt Timeout-Fehler ab.
                                     # Catches timeout errors.
            print(f"Timeout beim Abrufen von {url}") # Gibt den Timeout-Fehler aus.
                                                      # Prints the timeout error.
            self.reporter.add_broken_link(url, 0, "Crawler Fetch Timeout") # Meldet den Link als defekt.
                                                                           # Reports the link as broken.
            return None
        except Exception as e: # Fängt alle anderen unerwarteten Fehler ab.
                               # Catches all other unexpected errors.
            print(f"Unerwarteter Fehler beim Abrufen von {url}: {e}") # Gibt den Fehler aus.
                                                                   # Prints the error.
            self.reporter.add_broken_link(url, 0, "Crawler Unexpected Error") # Meldet den Link als defekt.
                                                                              # Reports the link as broken.
            return None

    async def _crawl_worker(self, session: aiohttp.ClientSession, link_checker: LinkChecker):
        """
        Ein Worker, der URLs aus der Warteschlange holt und crawlt.
        A worker that fetches URLs from the queue and crawls them.
        """
        while True:
            current_url, current_depth = await self.to_visit_queue.get() # Holt eine URL und ihre Tiefe aus der Warteschlange.
                                                                       # Gets a URL and its depth from the queue.
            try:
                if current_url in self.visited_urls: # Überspringt bereits besuchte URLs.
                                                  # Skips already visited URLs.
                    continue

                self.visited_urls.add(current_url) # Markiert die URL als besucht.
                                                 # Marks the URL as visited.
                print(f"Crawling: {current_url} (Tiefe: {current_depth})") # Gibt die aktuell gecrawlte URL aus.
                                                                       # Prints the currently crawled URL.

                if current_depth >= self.max_depth: # Überprüft, ob die maximale Crawl-Tiefe erreicht wurde.
                                                   # Checks if the maximum crawl depth has been reached.
                    continue

                html_content = await self._fetch_and_parse_page(session, current_url) # Holt und parst die Seite.
                                                                                     # Fetches and parses the page.
                if html_content:
                    link_extractor = LinkExtractor(current_url) # Erstellt einen LinkExtractor für die aktuelle URL.
                                                                # Creates a LinkExtractor for the current URL.
                    found_links = link_extractor.extract_links(html_content) # Extrahiert Links aus dem HTML.
                                                                             # Extracts links from the HTML.

                    # Gleichzeitiges Überprüfen aller gefundenen Links
                    # Concurrently check all found links
                    check_tasks = [link_checker.check_link(link) for link in found_links]
                    checked_results = await asyncio.gather(*check_tasks) # Führt alle Link-Überprüfungen gleichzeitig aus.
                                                                       # Executes all link checks concurrently.

                    for link, status_code in checked_results:
                        if status_code >= 400 or status_code == 0: # Überprüft, ob der Link defekt ist (4xx/5xx oder Netzwerkfehler).
                                                                # Checks if the link is broken (4xx/5xx or network error).
                            self.reporter.add_broken_link(link, status_code, current_url) # Meldet den defekten Link.
                                                                                          # Reports the broken link.
                        
                        # Füge nur Links zur Warteschlange hinzu, die zur gleichen Domain gehören und noch nicht besucht wurden
                        # Only add links to the queue that belong to the same domain and have not been visited yet
                        normalized_link = self._normalize_url(link)
                        if self._is_same_domain(normalized_link) and normalized_link not in self.visited_urls:
                            await self.to_visit_queue.put((normalized_link, current_depth + 1)) # Fügt den Link zur Warteschlange hinzu.
                                                                                                # Adds the link to the queue.

            finally:
                self.to_visit_queue.task_done() # Signalisiert, dass die Aufgabe abgeschlossen ist.
                                                # Signals that the task is done.

    async def run(self):
        """
        Startet den Crawling-Prozess.
        Starts the crawling process.
        """
        print(f"Starte Crawler von {self.start_url} mit max. Tiefe {self.max_depth} und {self.concurrency} gleichzeitigen Anfragen.")
        print("-------------------------------------------------------------------------------------------------------------------")
        
        async with aiohttp.ClientSession() as session: # Erstellt eine aiohttp ClientSession.
                                                      # Creates an aiohttp ClientSession.
            link_checker = LinkChecker(session)
            await self.to_visit_queue.put((self.start_url, 0)) # Fügt die Start-URL zur Warteschlange hinzu.
                                                             # Adds the start URL to the queue.

            workers = []
            for _ in range(self.concurrency): # Erstellt Worker-Aufgaben basierend auf der Parallelität.
                                              # Creates worker tasks based on concurrency.
                worker = asyncio.create_task(self._crawl_worker(session, link_checker))
                workers.append(worker)

            await self.to_visit_queue.join() # Wartet, bis alle Aufgaben in der Warteschlange abgeschlossen sind.
                                             # Waits until all tasks in the queue are done.

            for worker in workers: # Bricht alle Worker-Aufgaben ab.
                                   # Cancels all worker tasks.
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True) # Wartet auf den Abschluss der Abbruchvorgänge.
                                                                 # Waits for cancellation to complete.

        print("\nCrawl abgeschlossen.") # Crawler-Abschlussmeldung.
                                        # Crawler completion message.
        self.reporter.generate_report() # Generiert den Abschlussbericht.
                                        # Generates the final report.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asynchroner Web-Crawler zur Erkennung defekter Links.") # Argument-Parser-Beschreibung.
                                                                                                       # Argument parser description.
    parser.add_argument("start_url", type=str, help="Die Start-URL für den Crawl.") # Argument für die Start-URL.
                                                                                 # Argument for the start URL.
    parser.add_argument("--max-depth", type=int, default=1, help="Die maximale Tiefe, bis zu der der Crawler Links verfolgen soll (Standard: 1).") # Argument für die maximale Tiefe.
                                                                                                                                              # Argument for max depth.
    parser.add_argument("--concurrency", type=int, default=5, help="Die maximale Anzahl gleichzeitiger HTTP-Anfragen (Standard: 5).") # Argument für die Parallelität.
                                                                                                                                  # Argument for concurrency.

    args = parser.parse_args()

    crawler = AsyncWebCrawler(
        start_url=args.start_url,
        max_depth=args.max_depth,
        concurrency=args.concurrency
    )
    asyncio.run(crawler.run()) # Startet den asynchronen Crawling-Prozess.
                               # Starts the asynchronous crawling process.
