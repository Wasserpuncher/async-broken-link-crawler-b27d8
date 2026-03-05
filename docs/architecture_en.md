# Architecture Overview: Async Broken Link Crawler

## Introduction
The Async Broken Link Crawler is designed for efficiency and scalability, utilizing Python's `asyncio` framework for concurrent operations. Its modular architecture allows for easy maintenance, testing, and future enhancements. This document outlines the key components and their interactions.

## Core Components
The system is primarily composed of the following modules:

1.  **`LinkExtractor`**
    *   **Purpose**: Responsible for parsing HTML content and extracting all discoverable hyperlinks (`<a>` tags with `href` attributes).
    *   **Technology**: Uses `BeautifulSoup4` for robust HTML parsing.
    *   **Input**: Raw HTML content (string).
    *   **Output**: A list of absolute URLs found within the HTML.

2.  **`LinkChecker`**
    *   **Purpose**: Performs asynchronous HTTP requests to a given URL and determines its status (e.g., valid, broken, redirect).
    *   **Technology**: Leverages `aiohttp` for high-performance asynchronous HTTP client operations.
    *   **Input**: A URL (string).
    *   **Output**: A tuple containing the URL and its HTTP status code (or an error indicator if the request fails).
    *   **Error Handling**: Catches network errors (`aiohttp.ClientError`) and returns a specific status (e.g., 0 for network issues).

3.  **`BrokenLinkReporter`**
    *   **Purpose**: Collects and reports broken links. This component can be extended to support various output formats (console, file, database).
    *   **Input**: Broken link information (URL, status code, source page).
    *   **Output**: Formatted report (currently prints to console).
    *   **State Management**: Stores a list of unique broken links to avoid duplicate reporting.

4.  **`AsyncWebCrawler`**
    *   **Purpose**: The orchestrator of the entire crawling process. It manages the queue of URLs to visit, tracks visited URLs, and coordinates between `LinkExtractor`, `LinkChecker`, and `BrokenLinkReporter`.
    *   **Technology**: Built on `asyncio` for task management and `asyncio.Semaphore` for controlling concurrency.
    *   **Key Methods**:
        *   `__init__`: Initializes the crawler with a starting URL, maximum depth, and concurrency limit.
        *   `_fetch_and_parse_page`: Fetches a page, extracts links, and returns both the page content and the extracted links.
        *   `_check_link`: Asynchronously checks a single link using `LinkChecker`.
        *   `_crawl_page`: The core recursive function that fetches a page, extracts its links, adds new links to the queue, and schedules checks for all extracted links.
        *   `run`: The main entry point to start the crawling process. It initializes the queue and manages the worker tasks.
    *   **State Management**: Uses a `set` for `visited_urls` to prevent redundant processing and infinite loops, and an `asyncio.Queue` for managing URLs to be crawled.

## Asynchronous Nature
The project's performance heavily relies on `asyncio` and `aiohttp`:
-   **`asyncio.gather`**: Used to run multiple `LinkChecker` tasks concurrently for all links found on a single page.
-   **`asyncio.Semaphore`**: Limits the number of concurrent HTTP requests to prevent overwhelming the target server and manage resource utilization.
-   **`asyncio.Queue`**: Facilitates a producer-consumer pattern where `_crawl_page` functions produce new URLs, and worker tasks consume them.

## Data Flow and Interaction
1.  The `AsyncWebCrawler.run()` method initializes the crawling process by adding the `start_url` to an `asyncio.Queue`.
2.  Multiple worker tasks (limited by `concurrency_limit`) are spawned, each continuously pulling URLs from the queue.
3.  For each URL, a worker task calls `_crawl_page`:
    a.  It fetches the HTML content using `aiohttp`.
    b.  `LinkExtractor` parses the HTML to find new links.
    c.  Each extracted link is then checked by `LinkChecker` concurrently.
    d.  If a link is broken, `BrokenLinkReporter` records it.
    e.  New, unvisited, and in-scope links are added back to the `asyncio.Queue` for further crawling.
4.  The process continues until the queue is empty and all tasks are complete, respecting the `max_depth` and `concurrency_limit`.

## Error Handling
-   **HTTP Errors**: `LinkChecker` returns the actual HTTP status code, allowing `AsyncWebCrawler` to identify 4xx/5xx errors as broken links.
-   **Network Errors**: `aiohttp.ClientError` is caught during fetching, and these links are reported with a special error status.
-   **Timeout**: `aiohttp` client session can be configured with timeouts to prevent tasks from hanging indefinitely.

## Extensibility
-   **Reporting**: The `BrokenLinkReporter` can be easily extended to support different output formats (e.g., JSON, CSV, database).
-   **Link Filtering**: Additional logic can be added to `LinkExtractor` or `AsyncWebCrawler` to filter links based on domains, file types, or specific patterns.
-   **Authentication**: `aiohttp` client sessions can be configured with authentication headers for crawling protected sites.

## Scalability Considerations
-   **Concurrency**: The `asyncio.Semaphore` ensures controlled concurrency, preventing resource exhaustion.
-   **Memory Usage**: Tracking `visited_urls` with a `set` is efficient. For extremely large crawls, persistent storage (e.g., Redis) might be considered for visited URLs and queues.
-   **Distributed Crawling**: While currently single-node, the modular design makes it adaptable for distributed setups (e.g., using a shared queue like RabbitMQ or Kafka).

This architecture provides a solid foundation for a robust and efficient broken link detection system, ready for enterprise-level deployment.