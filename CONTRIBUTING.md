# Contributing to Async Broken Link Crawler

We welcome contributions from everyone! Whether you're fixing a bug, adding a new feature, improving documentation, or just asking a question, your involvement is valuable. Please take a moment to review this document to make the contribution process as smooth as possible.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Code Contributions](#code-contributions)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [License](#license)

## Code of Conduct
Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## How to Contribute

### Reporting Bugs
If you find a bug, please open an issue on the [GitHub Issues page](https://github.com/your-username/async-broken-link-crawler/issues) and provide the following information:

-   A clear and concise description of the bug.
-   Steps to reproduce the behavior.
-   Expected behavior.
-   Actual behavior.
-   Screenshots or error messages if applicable.
-   Your operating system and Python version.

### Suggesting Enhancements
Have an idea for a new feature or an improvement to an existing one? We'd love to hear it! Please open an issue on the [GitHub Issues page](https://github.com/your-username/async-broken-link-crawler/issues) and describe your suggestion in detail. Explain why it would be useful and how it might work.

### Code Contributions
We appreciate code contributions! To contribute code, please follow these steps:

1.  **Fork the repository.**
2.  **Clone your forked repository:**
    ```bash
    git clone https://github.com/your-username/async-broken-link-crawler.git
    cd async-broken-link-crawler
    ```
3.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b bugfix/issue-description
    ```
4.  **Make your changes.** Ensure your code adheres to our [Coding Guidelines](#coding-guidelines) and passes all [Tests](#testing).
5.  **Commit your changes** using descriptive [Commit Messages](#commit-messages).
6.  **Push your branch** to your forked repository:
    ```bash
    git push origin feature/your-feature-name
    ```
7.  **Open a Pull Request** against the `main` branch of the original repository. Provide a clear description of your changes and reference any related issues.

## Development Setup

1.  **Install Python 3.9+** (if not already installed).
2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate # On macOS/Linux
    # .venv\Scripts\activate   # On Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install pytest pytest-asyncio # For running tests
    ```

## Coding Guidelines

-   **PEP 8**: Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style.
-   **Type Hints**: Use [type hints](https://docs.python.org/3/library/typing.html) for function arguments and return values.
-   **Docstrings**: All public functions, methods, and classes should have clear docstrings following the [Google style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
-   **Comments**: Use inline comments (`#`) to explain complex logic, especially in German as required for this project.
-   **Variable Names**: Use descriptive English variable names.

## Testing

-   All new features and bug fixes should be accompanied by appropriate unit tests.
-   Tests are located in `test_main.py`.
-   To run tests:
    ```bash
    pytest
    # or
    python -m unittest discover
    ```
-   Ensure all tests pass before submitting a Pull Request.

## Commit Messages
Please follow the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/) for your commit messages. This helps us generate release notes and understand the history of changes.

Examples:

-   `feat: Add new concurrency limit option`
-   `fix: Correct broken link reporting for timeouts`
-   `docs: Update architecture diagram`
-   `refactor: Improve LinkExtractor regex performance`

## License
By contributing to Async Broken Link Crawler, you agree that your contributions will be licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.