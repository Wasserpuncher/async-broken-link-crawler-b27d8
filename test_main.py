import unittest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from main import LinkExtractor, LinkChecker, BrokenLinkReporter, AsyncWebCrawler
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
        self.assertEqual(crawler._normalize_url("https://test.com/page#fragment"), "https://test.com/page") # Entfernt Fragmente.
                                                                                                          # Removes fragments.
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

    @patch('builtins.print')
    async def test_crawler_single_page_no_broken_links(self, mock_print):
        """
        Testet den Crawler für eine einzelne Seite ohne defekte Links.
        Tests the crawler for a single page with no broken links.
        """
        crawler = AsyncWebCrawler(self.start_url, max_depth=1, concurrency=1)
        crawler.reporter = BrokenLinkReporter() # Stellt sicher, dass ein echter Reporter verwendet wird.
                                                # Ensures a real reporter is used.

        # Mock-Antwort für die Start-URL
        # Mock response for the start URL
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text.return_value = "<html><body><a href=\"/link1\">Link 1</a></body></html>"
        self.mock_session.get.return_value.__aenter__.return_value = mock_response

        # Mock LinkChecker, um nur OK-Status zurückzugeben
        # Mock LinkChecker to return only OK status
        self.mock_link_checker.check_link.side_effect = [
            (self.start_url + "link1", 200) # Simuliert einen erfolgreichen Check für den gefundenen Link.
                                           # Simulates a successful check for the found link.
        ]

        # Ersetzen Sie die Instanz von LinkChecker im Crawler
        # Replace the LinkChecker instance in the crawler
        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            async with aiohttp.ClientSession() as session_mock:
                crawler.session = session_mock # Setzt die Session des Crawlers auf das Mock-Objekt.
                                             # Sets the crawler's session to the mock object.
                await crawler.run()

        self.mock_session.get.assert_called_once_with(self.start_url + '/', allow_redirects=True, timeout=10) # Überprüft den Aufruf der GET-Methode für die Start-URL.
                                                                                                               # Checks the GET method call for the start URL.
        self.mock_link_checker.check_link.assert_called_once_with(self.start_url + "link1") # Überprüft den Aufruf der Link-Überprüfung.
                                                                                            # Checks the link check call.
        self.assertEqual(len(crawler.reporter.broken_links), 0) # Erwartet keine defekten Links.
                                                               # Expects no broken links.
        mock_print.assert_any_call("Keine defekten Links gefunden. Wunderbar!") # Überprüft die Erfolgsmeldung.
                                                                               # Checks the success message.

    @patch('builtins.print')
    async def test_crawler_single_page_with_broken_link(self, mock_print):
        """
        Testet den Crawler für eine einzelne Seite mit einem defekten Link.
        Tests the crawler for a single page with a broken link.
        """
        crawler = AsyncWebCrawler(self.start_url, max_depth=1, concurrency=1)
        crawler.reporter = BrokenLinkReporter() # Stellt sicher, dass ein echter Reporter verwendet wird.
                                                # Ensures a real reporter is used.

        # Mock-Antwort für die Start-URL
        # Mock response for the start URL
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text.return_value = "<html><body><a href=\"/broken-link\">Broken Link</a></body></html>"
        self.mock_session.get.return_value.__aenter__.return_value = mock_response

        # Mock LinkChecker, um einen defekten Link zurückzugeben
        # Mock LinkChecker to return a broken link
        self.mock_link_checker.check_link.side_effect = [
            (self.start_url + "broken-link", 404) # Simuliert einen defekten Link.
                                                  # Simulates a broken link.
        ]

        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            async with aiohttp.ClientSession() as session_mock:
                crawler.session = session_mock
                await crawler.run()

        self.assertEqual(len(crawler.reporter.broken_links), 1) # Erwartet einen defekten Link.
                                                               # Expects one broken link.
        self.assertIn((self.start_url + "broken-link", 404, self.start_url + '/'), crawler.reporter.broken_links) # Überprüft den defekten Link im Bericht.
                                                                                                               # Checks the broken link in the report.
        mock_print.assert_any_call("[DEFEKT] Status: 404 - Link: https://test.com/broken-link (gefunden auf: https://test.com/)") # Überprüft die Ausgabe des defekten Links.
                                                                                                                              # Checks the output of the broken link.

    @patch('builtins.print')
    async def test_crawler_max_depth(self, mock_print):
        """
        Testet den Crawler mit maximaler Tiefe.
        Tests the crawler with maximum depth.
        """
        # Start-URL -> Link1 (Tiefe 0 -> 1)
        # Link1 -> Link2 (Tiefe 1 -> 2) - sollte nicht gecrawlt werden, da max_depth=1

        crawler = AsyncWebCrawler(self.start_url, max_depth=1, concurrency=1)
        crawler.reporter = BrokenLinkReporter()

        # Mock-Antworten für Seiten und Link-Checks
        # Mock responses for pages and link checks
        async def mock_get_side_effect(url, **kwargs):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            if url == self.start_url + '/':
                mock_response.text.return_value = f"<html><body><a href=\"{self.start_url}/link1\">Link 1</a></body></html>"
            elif url == self.start_url + '/link1':
                mock_response.text.return_value = f"<html><body><a href=\"{self.start_url}/link2\">Link 2</a></body></html>"
            else:
                mock_response.raise_for_status()
            return mock_response

        self.mock_session.get.side_effect = mock_get_side_effect

        self.mock_link_checker.check_link.side_effect = [
            (self.start_url + "link1", 200),  # Link1 von Start-URL
            (self.start_url + "link2", 200)   # Link2 von Link1 (wird geprüft, aber nicht gecrawlt)
        ]

        with patch('main.LinkChecker', return_value=self.mock_link_checker):
            async with aiohttp.ClientSession() as session_mock:
                crawler.session = session_mock
                await crawler.run()

        # Crawler sollte https://test.com/ und https://test.com/link1 besuchen
        # The crawler should visit https://test.com/ and https://test.com/link1
        self.assertIn(self.start_url + '/', crawler.visited_urls)
        self.assertIn(self.start_url + '/link1', crawler.visited_urls)

        # Aber Link2 sollte nicht gecrawlt werden (d.h. nicht in visited_urls sein), da max_depth=1
        # But Link2 should not be crawled (i.e., not in visited_urls) because max_depth=1
        self.assertNotIn(self.start_url + '/link2', crawler.visited_urls)

        # Die GET-Methode sollte für Start-URL und Link1 aufgerufen werden
        # The GET method should be called for start URL and Link1
        self.assertEqual(self.mock_session.get.call_count, 2) # Überprüft, ob GET zweimal aufgerufen wurde.
                                                               # Checks if GET was called twice.
        self.mock_session.get.assert_any_call(self.start_url + '/', allow_redirects=True, timeout=10)
        self.mock_session.get.assert_any_call(self.start_url + '/link1', allow_redirects=True, timeout=10)

        # LinkChecker sollte für Link1 und Link2 aufgerufen werden
        # LinkChecker should be called for Link1 and Link2
        self.assertEqual(self.mock_link_checker.check_link.call_count, 2) # Überprüft, ob check_link zweimal aufgerufen wurde.
                                                                         # Checks if check_link was called twice.
        self.mock_link_checker.check_link.assert_any_call(self.start_url + "link1")
        self.mock_link_checker.check_link.assert_any_call(self.start_url + "link2")

        self.assertEqual(len(crawler.reporter.broken_links), 0) # Erwartet keine defekten Links.
                                                               # Expects no broken links.


if __name__ == '__main__':
    unittest.main() # Führt alle Tests aus.
                     # Runs all tests.
