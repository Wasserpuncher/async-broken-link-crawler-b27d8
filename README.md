# Async Broken Link Crawler

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Table of Contents
- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## About
Welcome to the Async Broken Link Crawler! This project provides an enterprise-ready, high-performance asynchronous web-crawler designed to efficiently detect broken links across websites. Leveraging Python's `asyncio` and `aiohttp`, it can concurrently check thousands of links, making it ideal for large-scale web integrity checks.

## Features
- **Asynchronous Operations**: Utilizes `asyncio` for concurrent link checking, drastically reducing crawl times.
- **Scalable**: Built to handle large websites and numerous links without compromising performance.
- **Robust Error Handling**: Gracefully manages network errors, timeouts, and various HTTP status codes.
- **Customizable Depth**: Configure how deep the crawler should go into a website's link structure.
- **Comprehensive Reporting**: Generates a clear report of all broken links found.
- **Modular Design**: Easy to extend and integrate into existing systems.

## Installation
To get started with the Async Broken Link Crawler, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/async-broken-link-crawler.git
    cd async-broken-link-crawler
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage
Once installed, you can run the crawler from the command line. The `main.py` script serves as the entry point.

```bash
python main.py <start_url> [--max-depth <depth>] [--concurrency <num_workers>]
```

**Example:** Crawl `https://example.com` up to a depth of 2, using 10 concurrent requests:

```bash
python main.py https://example.com --max-depth 2 --concurrency 10
```

The crawler will print broken links directly to the console.

## Architecture
For a detailed understanding of the project's design and internal workings, please refer to our architectural documentation:
- [Architecture Overview (English)](./docs/architecture_en.md)
- [Architekturübersicht (Deutsch)](./docs/architecture_de.md)

## Contributing
We welcome contributions from the community! Whether it's bug reports, feature requests, or code contributions, your help is valuable. Please refer to our [CONTRIBUTING.md](./CONTRIBUTING.md) guide for detailed instructions on how to get involved.

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.