import unittest
import asyncio
import aiohttp
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from main import (
    LinkExtractor,
    LinkChecker,
    BrokenLinkReporter,
    AsyncWebCrawler,
    load_config,
    resolve_settings,
    DEFAULT_SETTINGS,
)
from urllib.parse import urlparse

class TestLinkExtractor(unittest.TestCase):
    """
    Testfälle für die LinkExtractor-Klasse.
    Test cases for the LinkExtractor class.
    """

    def test_extract_absolute_links(self):
        """
        Testet die Extraktion absoluter Links.
        Tests the extraction of absolute links.
        """
        base_url = "https://example.com/page/"
        html_content = """
        <html>
            <body>
                <a href="/other-page">Relative Link</a>
                <a href="https://example.com/another-page">Absolute Link</a>
                <a href="http://external.com/some-resource">External Link</a>
                <a href="#section">Anchor Link</a>
                <a href="invalid-link.html">Relative Link 2</a>
            </body>
        </html>
        """
        extractor = LinkExtractor(base_url)
        links = extractor.extract_links(html_content)
        expected_links = [
            "https://example.com/other-page",
            "https://example.com/another-page",
            "http://external.com/some-resource",
            "https://example.com/page/#section",
            "https://example.com/page/invalid-link.html"
        ]
        self.assertCountEqual(links, expected_links) # Überprüft, ob die extrahierten Links mit den erwarteten übereinstimmen.
                                                    # Checks if the extracted links match the expected ones.

    def test_no_links(self):
        """
        Testet die Extraktion von Links aus HTML ohne Links.
        Tests link extraction from HTML with no links.
        """
        base_url = "https://example.com"
        html_content = "<html><body><h1>No links here</h1></body></html>"
        extractor = LinkExtractor(base_url)
        links = extractor.extract_links(html_content)
        self.assertEqual(links, []) # Erwartet eine leere Liste, da keine Links vorhanden sind.
                                    # Expects an empty list as there are no links.

    def test_empty_html(self):
        """
        Testet die Extraktion von Links aus leerem HTML.
        Tests link extraction from empty HTML.
        """
        base_url = "https://example.com"
        html_content = ""
        extractor = LinkExtractor(base_url)
        links = extractor.extract_links(html_content)
        self.assertEqual(links, []) # Erwartet eine leere Liste.
                                    # Expects an empty list.


class TestLinkChecker(unittest.IsolatedAsyncioTestCase):
    """
    Testfälle für die LinkChecker-Klasse.
    Test cases for the LinkChecker class.
    """

    async def asyncSetUp(self):
        """
        Richtet die asynchrone Testumgebung ein.
        Sets up the asynchronous test environment.
        """
        self.mock_session = AsyncMock(spec=aiohttp.ClientSession) # Mockt die aiohttp.ClientSession.
                                                                # Mocks the aiohttp.ClientSession.
        self.link_checker = LinkChecker(self.mock_session)

    async def test_check_link_ok(self):
        """
        Testet die Überprüfung eines Links mit HTTP 200 OK.
        Tests checking a link with HTTP 200 OK.
        """
        mock_response = AsyncMock()
        mock_response.status = 200
        self.mock_session.get.return_value.__aenter__.return_value = mock_response # Simuliert eine erfolgreiche Antwort.
                                                                                 # Simulates a successful response.

        url = "https://example.com/ok"
        result_url, status = await self.link_checker.check_link(url)

        self.assertEqual(result_url, url) # Überprüft die zurückgegebene URL.
                                          # Checks the returned URL.
        self.assertEqual(status, 200) # Überprüft den Statuscode.
                                      # Checks the status code.
        self.mock_session.get.assert_called_once_with(url, allow_redirects=True, timeout=10) # Überprüft den Aufruf der GET-Methode.
                                                                                             # Checks the call to the GET method.

    async def test_check_link_broken(self):
        """
        Testet die Überprüfung eines Links mit HTTP 404 Not Found.
        Tests checking a link with HTTP 404 Not Found.
        """
        mock_response = AsyncMock()
        mock_response.status = 404
        self.mock_session.get.return_value.__aenter__.return_value = mock_response # Simuliert eine 404-Antwort.
                                                                                 # Simulates a 404 response.

        url = "https://example.com/broken"
        result_url, status = await self.link_checker.check_link(url)

        self.assertEqual(result_url, url) # Überprüft die zurückgegebene URL.
                                          # Checks the returned URL.
        self.assertEqual(status, 404) # Überprüft den Statuscode.
                                      # Checks the status code.

    async def test_check_link_client_error(self):
        """
        Testet die Fehlerbehandlung bei einem aiohttp.ClientError.
        Tests error handling for an aiohttp.ClientError.
        """
        self.mock_session.get.side_effect = aiohttp.ClientError("Connection refused") # Simuliert einen Client-Fehler.
                                                                                   # Simulates a client error.

        url = "https://example.com/error"
        result_url, status = await self.link_checker.check_link(url)

        self.assertEqual(result_url, url) # Überprüft die zurückgegebene URL.
                                          # Checks the returned URL.
        self.assertEqual(status, 0) # Erwartet Status 0 für Client-Fehler.
                                    # Expects status 0 for client errors.

    async def test_check_link_timeout_error(self):
        """
        Testet die Fehlerbehandlung bei einem asyncio.TimeoutError.
        Tests error handling for an asyncio.TimeoutError.
        """
        self.mock_session.get.side_effect = asyncio.TimeoutError # Simuliert einen Timeout-Fehler.
                                                                # Simulates a timeout error.

        url = "https://example.com/timeout"
        result_url, status = await self.link_checker.check_link(url)

        self.assertEqual(result_url, url) # Überprüft die zurückgegebene URL.
                                          # Checks the returned URL.
        self.assertEqual(status, 0) # Erwartet Status 0 für Timeout-Fehler.
                                    # Expects status 0 for timeout errors.


class TestBrokenLinkReporter(unittest.TestCase):
    """
    Testfälle für die BrokenLinkReporter-Klasse.
    Test cases for the BrokenLinkReporter class.
    """

    def setUp(self):
        """
        Richtet den Reporter für jeden Test ein.
        Sets up the reporter for each test.
        """
        self.reporter = BrokenLinkReporter()

    def test_add_broken_link(self):
        """
        Testet das Hinzufügen eines defekten Links.
        Tests adding a broken link.
        """
        self.reporter.add_broken_link("https://broken.com/404", 404, "https://source.com")
        self.assertIn(("https://broken.com/404", 404, "https://source.com"), self.reporter.broken_links) # Überprüft, ob der Link hinzugefügt wurde.
                                                                                                        # Checks if the link was added.

    def test_add_duplicate_broken_link(self):
        """
        Testet das Hinzufügen eines doppelten defekten Links (sollte nur einmal gespeichert werden).
        Tests adding a duplicate broken link (should only be stored once).
        """
        self.reporter.add_broken_link("https://broken.com/404", 404, "https://source.com")
        self.reporter.add_broken_link("https://broken.com/404", 404, "https://source.com") # Fügt den gleichen Link erneut hinzu.
                                                                                          # Adds the same link again.
        self.assertEqual(len(self.reporter.broken_links), 1) # Erwartet nur einen Eintrag.
                                                            # Expects only one entry.

    @patch('builtins.print')
    def test_generate_report_no_broken_links(self, mock_print):
        """
        Testet die Berichtserstellung, wenn keine defekten Links vorhanden sind.
        Tests report generation when no broken links are present.
        """
        self.reporter.generate_report()
        mock_print.assert_called_with("Keine defekten Links gefunden. Wunderbar!") # Überprüft die Ausgabe bei keinen defekten Links.
                                                                               # Checks the output when no broken links are found.

    @patch('builtins.print')
    def test_generate_report_with_broken_links(self, mock_print):
        """
        Testet die Berichtserstellung mit defekten Links.
        Tests report generation with broken links.
        """
        self.reporter.add_broken_link("https://broken.com/404", 404, "https://source.com/page1")
        self.reporter.add_broken_link("https://bad.com/500", 500, "https://source.com/page2")
        self.reporter.generate_report()

        # Überprüfen Sie, ob print mit den erwarteten Zeilen aufgerufen wurde (Reihenfolge kann variieren, daher die Überprüfung der Aufrufe)
        # Check if print was called with the expected lines (order may vary, so check calls)
        mock_print.assert_any_call("\n--- Bericht über defekte Links ---") # Überprüft den Header.
                                                                     # Checks the header.
        mock_print.assert_any_call("[DEFEKT] Status: 404 - Link: https://broken.com/404 (gefunden auf: https://source.com/page1)") # Überprüft den ersten defekten Link.
                                                                                                                            # Checks the first broken link.
        mock_print.assert_any_call("[DEFEKT] Status: 500 - Link: https://bad.com/500 (gefunden auf: https://source.com/page2)") # Überprüft den zweiten defekten Link.
                                                                                                                          # Checks the second broken link.
        mock_print.assert_any_call("----------------------------------") # Überprüft den Footer.
                                                                     # Checks the footer.


class TestAsyncWebCrawler(unittest.IsolatedAsyncioTestCase):
    """
    Testfälle für die AsyncWebCrawler-Klasse.
    Test cases for the AsyncWebCrawler class.
    """

    def setUp(self):
        """
        Richtet die Mock-Objekte ein.
        Sets up mock objects.
        """
        self.start_url = "https://test.com"
        self.mock_session = AsyncMock(spec=aiohttp.ClientSession)
        self.mock_link_checker = AsyncMock(spec=LinkChecker)
        self.mock_link_extractor = MagicMock(spec=LinkExtractor)

        # Patch LinkExtractor, um eine Instanz zurückzugeben, die wir kontrollieren können
        # Patch LinkExtractor to return an instance we can control
        patcher = patch('main.LinkExtractor', return_value=self.mock_link_extractor)
        self.addCleanup(patcher.stop)
        patcher.start()

    async def test_normalize_url(self):
        """
        Testet die URL-Normalisierung.
        Tests URL normalization.
        """
        crawler = AsyncWebCrawler(self.start_url)
        self.assertEqual(crawler._normalize_url("https://test.com"), "https://test.com/") # Normalisiert die Root-URL.
                                                                                        # Normalizes the root URL.
        # Fragmente werden entfernt; für ein Verzeichnis-artiges Segment (ohne Punkt)
        # wird konsistent ein Schrägstrich am Ende ergänzt (wie bei /path/to/dir unten).
        # Fragments are removed; a directory-like segment (no dot) consistently gets a
        # trailing slash (same rule as /path/to/dir below).
        self.assertEqual(crawler._normalize_url("https://test.com/page#fragment"), "https://test.com/page/")
        self.assertEqual(crawler._normalize_url("https://test.com/path/to/file.html"), "https://test.com/path/to/file.html") # Lässt Dateipfade unverändert.
                                                                                                                             # Leaves file paths unchanged.
        self.assertEqual(crawler._normalize_url("https://test.com/path/to/dir"), "https://test.com/path/to/dir/") # Fügt Schrägstrich am Ende für Verzeichnisse hinzu.
                                                                                                                # Adds trailing slash for directories.

    async def test_is_same_domain(self):
        """
        Testet die Domain-Überprüfung.
        Tests domain checking.
        """
        crawler = AsyncWebCrawler(self.start_url)
        self.assertTrue(crawler._is_same_domain("https://test.com/page")) # Gleiche Domain.
                                                                       # Same domain.
        self.assertTrue(crawler._is_same_domain("https://www.test.com/page")) # Gleiche Subdomain wird als gleiche Domain behandelt (könnte in der Realität komplexer sein).
                                                                            # Same subdomain treated as same domain (could be more complex in reality).
        self.assertFalse(crawler._is_same_domain("https://other.com")) # Andere Domain.
                                                                      # Different domain.

    def _bind_mock_session(self):
        """
        Patcht aiohttp.ClientSession so, dass run() die in setUp erzeugte
        gemockte Session verwendet. Gibt nichts zurück; der Patch wird am
        Testende automatisch entfernt.
        Patches aiohttp.ClientSession so that run() uses the mock session created
        in setUp. The patch is removed automatically at test teardown.
        """
        patcher = patch('main.aiohttp.ClientSession')
        mock_cls = patcher.start()
        self.addCleanup(patcher.stop)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=self.mock_session)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

    @staticmethod
    def _html_response(html: str):
        """
        Erzeugt einen asynchronen Context-Manager, der eine HTML-Antwort liefert
        (wie ihn session.get(...) zurückgibt).
        Builds an async context manager yielding an HTML response, as session.get(...)
        returns.
        """
        response = AsyncMock()
        response.status = 200
        response.headers = {'Content-Type': 'text/html'}
        response.text.return_value = html
        response.raise_for_status = MagicMock()  # Kein Fehler bei 2xx. / No error for 2xx.
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        return cm

    @patch('builtins.print')
    async def test_crawler_single_page_no_broken_links(self, mock_print):
        """
        Testet den Crawler für eine einzelne Seite ohne defekte Links.
        Tests the crawler for a single page with no broken links.
        """
        self._bind_mock_session()  # run() nutzt jetzt self.mock_session. / run() now uses self.mock_session.
        crawler = AsyncWebCrawler(self.start_url, max_depth=1, concurrency=1)
        crawler.reporter = BrokenLinkReporter()  # Echter Reporter. / Real reporter.

        # session.get(...) liefert immer die Start-Seite mit genau einem Link.
        # session.get(...) always returns the start page with exactly one link.
        self.mock_session.get.return_value = self._html_response(
            "<html><body><a href=\"/link1\">Link 1</a></body></html>"
        )
        # Der (gemockte) LinkExtractor gibt genau diesen Link zurück.
        # The (mocked) LinkExtractor returns exactly this link.
        self.mock_link_extractor.extract_links.return_value = [self.start_url + "/link1"]
        # Der gemockte LinkChecker meldet den Link als OK (200).
        # The mocked LinkChecker reports the link as OK (200).
        self.mock_link_checker.check_link.side_effect = [(self.start_url + "/link1", 200)]

        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            await crawler.run()

        # Nur die Start-URL (Tiefe 0) wird abgerufen; der Link (Tiefe 1) liegt auf max_depth.
        # Only the start URL (depth 0) is fetched; the link (depth 1) sits at max_depth.
        self.mock_session.get.assert_any_call(self.start_url + '/', allow_redirects=True, timeout=10)
        self.mock_link_checker.check_link.assert_called_once_with(self.start_url + "/link1")
        self.assertEqual(len(crawler.reporter.broken_links), 0)
        mock_print.assert_any_call("Keine defekten Links gefunden. Wunderbar!")

    @patch('builtins.print')
    async def test_crawler_single_page_with_broken_link(self, mock_print):
        """
        Testet den Crawler für eine einzelne Seite mit einem defekten Link.
        Tests the crawler for a single page with a broken link.
        """
        self._bind_mock_session()
        crawler = AsyncWebCrawler(self.start_url, max_depth=1, concurrency=1)
        crawler.reporter = BrokenLinkReporter()

        self.mock_session.get.return_value = self._html_response(
            "<html><body><a href=\"/broken-link\">Broken Link</a></body></html>"
        )
        self.mock_link_extractor.extract_links.return_value = [self.start_url + "/broken-link"]
        # Der gemockte LinkChecker meldet den Link als defekt (404).
        # The mocked LinkChecker reports the link as broken (404).
        self.mock_link_checker.check_link.side_effect = [(self.start_url + "/broken-link", 404)]

        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            await crawler.run()

        self.assertEqual(len(crawler.reporter.broken_links), 1)
        # Der Bericht enthält den defekten Link mit Status und Quellseite (die Start-URL).
        # The report contains the broken link with status and source page (the start URL).
        self.assertIn(
            (self.start_url + "/broken-link", 404, self.start_url + '/'),
            crawler.reporter.broken_links
        )
        mock_print.assert_any_call(
            "[DEFEKT] Status: 404 - Link: https://test.com/broken-link (gefunden auf: https://test.com/)"
        )

    @patch('builtins.print')
    async def test_crawler_max_depth(self, mock_print):
        """
        Testet, dass der Crawler die maximale Tiefe respektiert.
        Tests that the crawler respects the maximum depth.

        Bei max_depth=2 werden die Start-Seite (Tiefe 0) und link1 (Tiefe 1)
        abgerufen; link2 (Tiefe 2) wird noch geprüft, aber seine Seite wird nicht
        mehr abgerufen.
        With max_depth=2 the start page (depth 0) and link1 (depth 1) are fetched;
        link2 (depth 2) is still checked, but its page is not fetched anymore.
        """
        self._bind_mock_session()
        crawler = AsyncWebCrawler(self.start_url, max_depth=2, concurrency=1)
        crawler.reporter = BrokenLinkReporter()

        page0 = "<html><body>PAGE0<a href=\"/link1\">Link 1</a></body></html>"
        page1 = "<html><body>PAGE1<a href=\"/link2\">Link 2</a></body></html>"

        def get_side_effect(url, **kwargs):
            if url == self.start_url + '/':
                return self._html_response(page0)
            if url == self.start_url + '/link1/':
                return self._html_response(page1)
            # Sollte nicht erreicht werden; leere Seite als Absicherung. / Should not be reached.
            return self._html_response("<html><body>EMPTY</body></html>")

        self.mock_session.get.side_effect = get_side_effect

        # Der gemockte LinkExtractor liefert je nach Seiteninhalt den nächsten Link.
        # The mocked LinkExtractor yields the next link depending on the page content.
        def extract_side_effect(html_content):
            if "PAGE0" in html_content:
                return [self.start_url + "/link1"]
            if "PAGE1" in html_content:
                return [self.start_url + "/link2"]
            return []

        self.mock_link_extractor.extract_links.side_effect = extract_side_effect

        self.mock_link_checker.check_link.side_effect = [
            (self.start_url + "/link1", 200),  # von der Start-Seite / from the start page
            (self.start_url + "/link2", 200),  # von link1 / from link1
        ]

        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            await crawler.run()

        # Start-Seite und link1 werden besucht.
        # Start page and link1 are visited.
        self.assertIn(self.start_url + '/', crawler.visited_urls)
        self.assertIn(self.start_url + '/link1/', crawler.visited_urls)

        # Genau zwei Seiten werden abgerufen; link2 wird nicht abgerufen.
        # Exactly two pages are fetched; link2 is not fetched.
        self.assertEqual(self.mock_session.get.call_count, 2)
        fetched_urls = [call.args[0] for call in self.mock_session.get.call_args_list]
        self.assertIn(self.start_url + '/', fetched_urls)
        self.assertIn(self.start_url + '/link1/', fetched_urls)
        self.assertNotIn(self.start_url + '/link2/', fetched_urls)

        # Beide gefundenen Links werden geprüft.
        # Both discovered links are checked.
        self.assertEqual(self.mock_link_checker.check_link.call_count, 2)
        self.mock_link_checker.check_link.assert_any_call(self.start_url + "/link1")
        self.mock_link_checker.check_link.assert_any_call(self.start_url + "/link2")

        self.assertEqual(len(crawler.reporter.broken_links), 0)


class TestConfigFile(unittest.TestCase):
    """
    Testfälle für das Laden und Anwenden der JSON-Konfigurationsdatei.
    Test cases for loading and applying the JSON configuration file.
    """

    def _write_config(self, data):
        """Schreibt data als JSON in eine temporäre Datei. / Writes data as JSON to a temp file."""
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.addCleanup(os.remove, path)
        return path

    def test_load_config_reads_known_keys(self):
        """load_config liest bekannte Schlüssel und verwirft unbekannte."""
        path = self._write_config({
            "start_url": "https://example.com",
            "max_depth": 3,
            "concurrency": 8,
            "output_path": "report.txt",
            "unknown": "dropped",
        })
        config = load_config(path)
        self.assertEqual(config["start_url"], "https://example.com")
        self.assertEqual(config["max_depth"], 3)
        self.assertEqual(config["concurrency"], 8)
        self.assertEqual(config["output_path"], "report.txt")
        self.assertNotIn("unknown", config)

    def test_load_config_rejects_non_object(self):
        """load_config lehnt JSON ab, das kein Objekt ist."""
        path = self._write_config(["not", "an", "object"])
        with self.assertRaises(ValueError):
            load_config(path)

    def test_load_config_missing_file(self):
        """load_config wirft FileNotFoundError bei fehlender Datei."""
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/crawler.json")

    def test_resolve_settings_precedence(self):
        """Vorrang: Defaults < Config < CLI."""
        self.assertEqual(resolve_settings({}, {}), DEFAULT_SETTINGS)
        merged = resolve_settings({}, {"max_depth": 4, "concurrency": 2})
        self.assertEqual(merged["max_depth"], 4)
        self.assertEqual(merged["concurrency"], 2)
        # CLI überschreibt Config, None-Werte werden ignoriert.
        cli = {"max_depth": 1, "concurrency": None, "start_url": "https://cli.example"}
        config = {"max_depth": 9, "concurrency": 7, "start_url": "https://config.example"}
        merged2 = resolve_settings(cli, config)
        self.assertEqual(merged2["max_depth"], 1)
        self.assertEqual(merged2["concurrency"], 7)
        self.assertEqual(merged2["start_url"], "https://cli.example")

    def test_config_applied_to_crawler(self):
        """Ein aus Config-Werten gebauter Crawler übernimmt diese Werte."""
        config = load_config(self._write_config({
            "start_url": "https://example.com",
            "max_depth": 5,
            "concurrency": 3,
            "output_path": "out.txt",
        }))
        settings = resolve_settings({}, config)

        # AsyncWebCrawler.__init__ erzeugt eine asyncio.Queue/Semaphore und benötigt
        # daher einen laufenden Event-Loop (Python 3.9). Instanziierung in asyncio.run.
        # AsyncWebCrawler.__init__ creates an asyncio.Queue/Semaphore and thus needs a
        # running event loop (Python 3.9). Instantiate inside asyncio.run.
        async def build():
            return AsyncWebCrawler(
                start_url=settings["start_url"],
                max_depth=settings["max_depth"],
                concurrency=settings["concurrency"],
                output_path=settings["output_path"],
            )
        crawler = asyncio.run(build())

        self.assertEqual(crawler.max_depth, 5)
        self.assertEqual(crawler.concurrency, 3)
        self.assertEqual(crawler.output_path, "out.txt")
        self.assertEqual(crawler.start_url, "https://example.com/")


class TestReportOutput(unittest.TestCase):
    """
    Testfälle für die Berichtsausgabe in eine Datei (aus der Config-Option output_path).
    Test cases for writing the report to a file (from the output_path config option).
    """

    def test_report_written_to_file(self):
        """generate_report schreibt die defekten Links in die angegebene Datei."""
        reporter = BrokenLinkReporter()
        reporter.add_broken_link("https://broken.com/404", 404, "https://source.com/page")
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        self.addCleanup(os.remove, path)

        reporter.generate_report(output_path=path)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("[DEFEKT] Status: 404 - Link: https://broken.com/404", content)
        self.assertIn("https://source.com/page", content)

    def test_report_file_no_broken_links(self):
        """Ohne defekte Links wird die Erfolgsmeldung in die Datei geschrieben."""
        reporter = BrokenLinkReporter()
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        self.addCleanup(os.remove, path)

        reporter.generate_report(output_path=path)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Keine defekten Links gefunden", content)


if __name__ == '__main__':
    unittest.main() # Führt alle Tests aus.
                     # Runs all tests.
