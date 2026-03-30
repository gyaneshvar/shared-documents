import os
import asyncio
import re
from playwright.async_api import async_playwright
import httpx

# Configuration
BASE_URL = "https://egazette.gov.in/"
OUTPUT_DIR = "pdfs"
MAX_DOWNLOADS = 300  
CONCURRENT_DOWNLOADS = 6  # Number of parallel downloads

# Semaphore to limit concurrency
download_semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)

async def download_file(url, filename, output_dir):
    """Download a file with error handling and concurrency control."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"Skipping existing file: {filename}")
        return "SKIPPED"

    async with download_semaphore:
        print(f"Downloading: {url} -> {filepath}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"Successfully saved {filepath}")
                return "SUCCESS"
            except Exception as e:
                print(f"Failed to download {url}: {e}")
                return "FAILED"

async def process_category(page, view_all_id, category_label, output_subdir, max_limit):
    """Process a single gazette category across all pages."""
    print(f"\n{'='*20} Starting {category_label} {'='*20}")
    
    # 1. Navigate to category page
    try:
        print(f"Clicking '{category_label}' View All...")
        await page.locator(f"#{view_all_id}").click()
        await page.wait_for_selector("#gvGazetteList tr", timeout=120000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Failed to load {category_label} list: {e}")
        return 0

    downloaded_in_category = 0
    current_page = 1
    
    while downloaded_in_category < max_limit:
        # Wait for table rows to load
        await page.wait_for_selector("#gvGazetteList tr", timeout=60000)
        await page.wait_for_timeout(2000)
        
        rows = await page.locator("#gvGazetteList tr").all()
        print(f"--- {category_label} | Page {current_page} ({len(rows)} rows) ---")
        
        # Paginate info
        pager_links = await page.locator("#gvGazetteList .pager a, #gvGazetteList tr:last-child a").all()
        page_numbers = []
        for link in pager_links:
            text = (await link.inner_text()).strip()
            if text.isdigit():
                page_numbers.append(int(text))
        max_page = max(page_numbers) if page_numbers else current_page

        # Extract data
        page_matches = []
        for row in rows:
            cells = await row.locator("td").all()
            if len(cells) < 9:
                continue
            
            texts = [(await c.inner_text()).strip() for c in cells]
            gazette_id = next((t for t in texts if any(x in t for x in ["CG-", "SG-", "CG_"])), "")
            publish_date = next((t for t in texts if re.search(r"\d{2}-\w{3}-\d{4}", t)), "")
            
            if not gazette_id and len(texts) >= 9:
                gazette_id = texts[8]
                publish_date = texts[7]

            year_match = re.search(r"\d{4}", publish_date)
            suffix_match = re.search(r"(\d+)$", gazette_id.replace(".pdf", ""))
            
            if year_match and suffix_match:
                year = year_match.group(0)
                id_suffix = suffix_match.group(1)
                pdf_url = f"{BASE_URL}WriteReadData/{year}/{id_suffix}.pdf"
                # Clean filename
                clean_id = gazette_id.replace('-', '_').replace(' ', '_').split('.')[0]
                filename = f"{clean_id}.pdf"
                page_matches.append((pdf_url, filename))

        # Download in parallel for the current page
        remaining_budget = max_limit - downloaded_in_category
        tasks = [download_file(url, fname, os.path.join(OUTPUT_DIR, output_subdir)) 
                 for url, fname in page_matches[:remaining_budget]]
        
        results = await asyncio.gather(*tasks)
        
        # Count successful downloads
        for res in results:
            if res == "SUCCESS":
                downloaded_in_category += 1

        if downloaded_in_category >= max_limit:
            break
            
        # Next page
        if current_page < max_page:
            next_page_num = current_page + 1
            next_page_link = page.locator(f"#gvGazetteList a:text('{next_page_num}')").first
            if await next_page_link.count() > 0:
                await next_page_link.click()
                current_page = next_page_num
                await page.wait_for_timeout(2000)
            else:
                break
        else:
            break

    print(f"Finished {category_label}. New downloads: {downloaded_in_category}")
    return downloaded_in_category

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()

        # Phase 1: Extra Ordinary Gazettes
        success = False
        for attempt in range(3):
            try:
                print(f"Navigating to {BASE_URL} (Attempt {attempt+1})...")
                await page.goto(BASE_URL, wait_until="load", timeout=120000)
                
                # Check for lnk_Extra_All for Extra Ordinary
                await process_category(page, "lnk_Extra_All", "Extra-Ordinary", "RecentExtraOrdinaryGazettes", MAX_DOWNLOADS)
                
                # Phase 2: Return Home and do Weekly Gazettes
                print("\nReturning Home for Weekly Gazettes...")
                await page.goto(BASE_URL, wait_until="load", timeout=120000)
                await process_category(page, "lnk_Week_All", "Weekly", "RecentWeeklyGazettes", MAX_DOWNLOADS)
                
                success = True
                break
            except Exception as e:
                print(f"Top-level error: {e}")
                await page.wait_for_timeout(5000)

        await browser.close()
        print("\nAll tasks complete!")

if __name__ == "__main__":
    asyncio.run(main())
