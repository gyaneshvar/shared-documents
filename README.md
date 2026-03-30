# eGazette PDF Downloader (Playwright Agent)

A robust Python-based automation tool to download gazette PDFs from `egazette.gov.in`. This script is designed to handle ASP.NET complexity, session states, and site-wide pagination.

## Features
- **Headless Browser:** Uses Playwright (Chromium) to handle dynamic ASP.NET content.
- **Parallel Downloads:** Downloads multiple PDFs simultaneously (default: 6) using `asyncio` semaphores for maximum speed.
- **Dual-Category Support:** Automatically processes both **Extra Ordinary** and **Weekly** gazettes in one run.
- **Auto-Pagination:** Navigates through multiple pages (Page 1, 2, 3...) for each category.
- **Smart Duplicate Check:** Skips files already present in the folder, ensuring you only download new content.
- **Organized Storage:** Automatically sorts PDFs into `RecentExtraOrdinaryGazettes` and `RecentWeeklyGazettes` subdirectories.

## Prerequisites
- Python 3.8 or higher.
- `pip` (Python package manager).

## Setup Instructions

1. **Create and Activate Virtual Environment (Recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate   # On Windows
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Browser Binaries:**
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Run
Execute the script to start the multi-category parallel download:
```bash
python3 download_playwright.py
```

### Configuration
Update these variables at the top of `download_playwright.py`:
- `MAX_DOWNLOADS`: Total new files to acquire per category (default: 300).
- `CONCURRENT_DOWNLOADS`: Number of files to download in parallel (default: 6).
- `OUTPUT_DIR`: Root folder for storing PDFs.

## Troubleshooting
- **Timeout Errors:** If the script times out frequently, the site might be under heavy load. The current timeout is set to 2 minutes per page.
- **No Pages Found:** Ensure you are connected to the internet and `egazette.gov.in` is accessible in your standard browser.
