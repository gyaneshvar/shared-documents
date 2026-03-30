import os
import asyncio
import re
import json
from datetime import datetime
from playwright.async_api import async_playwright
import httpx

# Configuration
BASE_URL = "https://egazette.gov.in/"
OUTPUT_DIR = os.path.join("pdfs", "seaweed_search")
TIMEOUT = 120000  # 2 minutes timeout for slow site
SEARCH_TERM = "seaweed"
CONCURRENT_DOWNLOADS = 5

# Semaphore to limit concurrency
download_semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)

async def download_file(url, filename, metadata, output_dir):
    """Download a PDF and save it along with its JSON metadata."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    json_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.json")

    if os.path.exists(filepath) and os.path.exists(json_path):
        print(f"Skipping existing file: {filename}")
        return "SKIPPED"

    async with download_semaphore:
        print(f"Downloading: {url} -> {filepath}")
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    # Update metadata with download details
                    metadata["download_url"] = url
                    metadata["downloaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    with open(json_path, "w", encoding="utf-8") as jf:
                        json.dump(metadata, jf, indent=4)
                    
                    print(f"Successfully saved {filename} and metadata.")
                    return "SUCCESS"
                else:
                    print(f"Failed to download {url}: HTTP {response.status_code}")
                    return "FAILED"
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                return "FAILED"

async def extract_row_data(page, index):
    """Extract all relevant metadata from a table row using span IDs."""
    data = {}
    try:
        # Define fields and their corresponding span ID fragments
        fields = {
            "govt_category": f"gvGazetteList_lbl_GovtCategory_{index}",
            "ministry": f"gvGazetteList_lbl_Ministry_{index}",
            "department": f"gvGazetteList_lbl_Department_{index}",
            "office": f"gvGazetteList_lbl_Office_{index}",
            "category": f"gvGazetteList_lbl_Category_{index}",
            "part_section": f"gvGazetteList_lbl_PartSection_{index}",
            "subject": f"gvGazetteList_lbl_Subject_{index}",
            "publish_date": f"gvGazetteList_lbl_PublishDate_{index}",
            "ugid": f"gvGazetteList_lbl_UGID_{index}",
            "size": f"gvGazetteList_lbl_GazetteSize_{index}"
        }

        for key, span_id in fields.items():
            element = page.locator(f"#{span_id}").first
            if await element.count() > 0:
                data[key] = (await element.inner_text()).strip()
            else:
                data[key] = ""
        
        return data
    except Exception as e:
        print(f"Error extracting data for row {index}: {e}")
        return None

async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            print(f"Navigating to {BASE_URL}...")
            await page.goto(BASE_URL, wait_until="networkidle", timeout=TIMEOUT)

            # Click Search
            print("Clicking 'Search' link...")
            await page.click("#sgzt")

            # Click Search by TEXT
            print("Clicking 'Search by TEXT' button...")
            await page.wait_for_selector("#btneSearch", state="visible")
            await page.click("#btneSearch")

            # Fill 'seaweed'
            print(f"Filling search term: '{SEARCH_TERM}'...")
            await page.wait_for_selector("#txtGazetteText", state="visible")
            await page.fill("#txtGazetteText", SEARCH_TERM)

            # Click Submit
            print("Clicking Submit...")
            await page.click("#Img_SubmitText")

            # Wait for results or empty message
            print("Waiting for results table...")
            try:
                # Wait for at least one UGID label to appear
                await page.wait_for_selector("#gvGazetteList_lbl_UGID_0", timeout=60000)
            except:
                print("Results table not found or timed out. Checking for 'No Record Found'.")
                content = await page.content()
                if "No Record Found" in content:
                    print("No records found for the search term.")
                    return
                else:
                    print("Timed out waiting for results.")
                    await page.screenshot(path="timeout_state.png")
                    return

            # Extract row data by looping through indices
            download_tasks = []
            index = 0
            
            while True:
                # Check if the UGID span for this index exists
                ugid_span = page.locator(f"#gvGazetteList_lbl_UGID_{index}").first
                if await ugid_span.count() == 0:
                    break # No more rows
                
                row_data = await extract_row_data(page, index)
                if not row_data or not row_data.get("ugid"):
                    index += 1
                    continue

                # Build URL: https://egazette.gov.in/WriteReadData/{year}/{ugid_suffix}.pdf
                ugid = row_data["ugid"]
                pub_date = row_data["publish_date"]
                
                # Suffix logic: extract last set of digits
                # Previous logic used: re.search(r"(\d+)$", ugid.strip())
                suffix_match = re.search(r"(\d+)$", ugid.strip())
                year_match = re.search(r"(\d{4})", pub_date)
                
                if year_match and suffix_match:
                    year = year_match.group(1)
                    suffix = suffix_match.group(1)
                    pdf_url = f"{BASE_URL}WriteReadData/{year}/{suffix}.pdf"
                    
                    # Construct filename: suffix_date.pdf
                    clean_date = pub_date.replace('-', '_')
                    filename = f"{suffix}_{clean_date}.pdf"
                    
                    download_tasks.append(download_file(pdf_url, filename, row_data, OUTPUT_DIR))
                
                index += 1

            if download_tasks:
                print(f"Starting {len(download_tasks)} downloads...")
                await asyncio.gather(*download_tasks)
            else:
                print("No downloadable items found.")

        except Exception as e:
            print(f"An error occurred: {e}")
            # Take a screenshot for debugging
            await page.screenshot(path="error_state.png")
            print("Saved error_state.png")
        finally:
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
