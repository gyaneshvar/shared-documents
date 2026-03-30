# eGazette PDF Downloader & Data Extractor

A robust Python-based automation toolkit to search, download, and extract structured data from the Indian eGazette portal (`egazette.gov.in`). Designed to handle slow site performance, complex ASP.NET session states, and bilingual document structures.

## Features

### 1. Automated Category Downloader (`download_playwright.py`)
- **Headless Browser:** Uses Playwright (Chromium) to handle dynamic content.
- **Dual-Category Support:** Processes both **Extra Ordinary** and **Weekly** gazettes.
- **Auto-Pagination:** Navigates through multiple results pages automatically.
- **Parallel Downloads:** Uses `asyncio` semaphores for concurrent PDF acquisition.

### 2. Targeted Search Downloader (`download_seaweed_search.py`)
- **Keyword Search:** Automates the "Search by TEXT" flow for specific keywords (e.g., "seaweed").
- **Rich Metadata Extraction:** Captures 10+ attributes for every result, including Ministry, Department, Subject, and UGID.
- **Sidecar JSON Generation:** Saves a detailed JSON metadata file for every downloaded PDF.
- **Slow-Site Optimized:** Implements 2-minute timeouts and robust retry logic for the portal's high latency.

### 3. Data Extraction Pipeline
- **Rule-Based Extraction:** Local parsing using `pdfplumber` for consistent table formats.
- **Vision AI Ready:** Architected to support VLM-based extraction (Gemini/GPT-4o) for complex bilingual layouts.

---

## Setup Instructions

1. **Create and Activate Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Usage

### Method A: Targeted Keyword Search (Recommended for specific topics)
To search for a specific term (default: "seaweed") and download all matching gazettes with metadata:
```bash
python3 download_seaweed_search.py
```
*Outputs to: `pdfs/seaweed_search/`*

### Method B: Bulk Category Download
To download recent gazettes by category (Extra-Ordinary/Weekly):
```bash
python3 download_playwright.py
```
*Outputs to: `pdfs/RecentExtraOrdinaryGazettes/` and `pdfs/RecentWeeklyGazettes/`*

---

## Output Format

### PDF & Metadata Pair
For every gazette found via search, the system saves two files:
1. `[UGID_SUFFIX]_[DATE].pdf` - The actual document.
2. `[UGID_SUFFIX]_[DATE].json` - Deep metadata including:
   - `govt_category`, `ministry`, `department`, `office`
   - `category`, `part_section`, `subject`
   - `publish_date`, `ugid`, `size`
   - `download_url`, `downloaded_at`

---

## Troubleshooting
- **Timeout Errors:** The eGazette portal is often slow. If the script fails, it will take an `error_state.png` screenshot for debugging. Timeouts are set to 120s by default.
- **Empty Results:** Ensure the search term matches at least one record on the portal. The script identifies "No Record Found" states.
- **Retry Logic:** If a parallel download fails, the script logs the error but continues with other files.
