# eGazette PDF Downloader (Playwright Agent)

A robust Python-based automation tool to download gazette PDFs from `egazette.gov.in`. This script is designed to handle ASP.NET complexity, session states, and site-wide pagination.

## Features
- **Headless Browser:** Uses Playwright (Chromium) to handle dynamic content.
- **Auto-Pagination:** Automatically navigates through multiple pages (Page 1, 2, 3...) to fulfill the download quota.
- **Duplicate Check:** Skips files that have already been downloaded to the `pdfs/` directory.
- **Retry Logic:** Includes built-in retries and long timeouts (2 minutes) to handle slow government server responses.
- **Agent Ready:** Structured for easy deployment on platforms like Modal.com.

## Prerequisites
- Python 3.8 or higher.
- `pip` (Python package manager).

## Setup Instructions

1. **Create and Activate Virtual Environment (Recommended):**
   This keeps your project dependencies isolated.
   ```bash
   # Create a virtual environment named .venv
   python3 -m venv .venv

   # Activate it (on macOS/Linux)
   source .venv/bin/activate

   # Activate it (on Windows)
   # .venv\Scripts\activate
   ```

2. **Install Dependencies:**
   Once the virtual environment is active, install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Browser Binaries:**
   Playwright requires specific browser binaries to run. Install Chromium with:
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Run
Execute the script to start downloading:
```bash
python3 download_playwright.py
```

### Configuration
You can modify the following variables at the top of `download_playwright.py`:
- `MAX_DOWNLOADS`: The total number of **new** PDF files you want to acquire (default: 30).
- `OUTPUT_DIR`: The local folder where PDFs will be stored (default: `pdfs`).
- `max_retries`: Number of attempts to connect if the site is slow.

## Troubleshooting
- **Timeout Errors:** If the script times out frequently, the site might be under heavy load. The current timeout is set to 2 minutes per page.
- **No Pages Found:** Ensure you are connected to the internet and `egazette.gov.in` is accessible in your standard browser.
