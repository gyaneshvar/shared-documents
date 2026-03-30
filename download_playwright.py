import os
import asyncio
import re
from playwright.async_api import async_playwright
import httpx

# Configuration
BASE_URL = "https://egazette.gov.in/"
OUTPUT_DIR = "pdfs"
MAX_DOWNLOADS = 30  # Increased to 10 as requested

async def download_file(url, filename):
    """Download a file with error handling."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Downloading: {url} -> {filepath}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"Successfully saved {filepath}")
            return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False

async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()

        max_retries = 3
        current_retry = 0
        success = False

        while current_retry < max_retries and not success:
            try:
                print(f"Attempt {current_retry + 1}: Navigating to {BASE_URL}...")
                # Timeout set to 120s (2 minutes)
                await page.goto(BASE_URL, wait_until="load", timeout=120000)

                # Step 1: Click 'View All' for 'Recent Extra Ordinary Gazettes'
                print("Clicking 'View All'...")
                view_all = page.locator("a:has-text('View All')").first
                await view_all.click()
                
                # Wait for the table to load on the next page (120s timeout)
                await page.wait_for_selector("#gvGazetteList", timeout=120000)
                print("Gazette list loaded successfully.")
                success = True
            except Exception as e:
                current_retry += 1
                print(f"Attempt {current_retry} failed: {e}")
                if current_retry < max_retries:
                    print(f"Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    print("Max retries reached. Exiting.")
                    await browser.close()
                    return

        # Step 2: Extract Gazette information across multiple pages
        downloaded_count = 0
        current_page = 1
        
        while downloaded_count < MAX_DOWNLOADS:
            # Wait for table rows to load on the current page
            await page.wait_for_selector("#gvGazetteList tr", timeout=120000)
            await page.wait_for_timeout(2000)
            
            rows = await page.locator("#gvGazetteList tr").all()
            print(f"--- Processing Page {current_page} ({len(rows)} rows found) ---")
            
            # 1. Identify total pages (only on the first pass or each page)
            pager_links = await page.locator("#gvGazetteList .pager a, #gvGazetteList tr:last-child a").all()
            page_numbers = []
            for link in pager_links:
                text = (await link.inner_text()).strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            max_page = max(page_numbers) if page_numbers else current_page
            if current_page == 1:
                print(f"Total pages detected: {max_page}")

            # 2. Extract gazettes from the current page
            page_matches = []
            for row in rows:
                cells = await row.locator("td").all()
                if len(cells) < 9:
                    continue
                
                texts = [(await c.inner_text()).strip() for c in cells]
                gazette_id = next((t for t in texts if "CG-" in t or "SG-" in t), "")
                publish_date = next((t for t in texts if re.search(r"\d{2}-\w{3}-\d{4}", t)), "")
                
                if not gazette_id and len(texts) >= 9:
                    gazette_id = texts[8]
                    publish_date = texts[7]

                year_match = re.search(r"\d{4}", publish_date)
                suffix_match = re.search(r"(\d+)$", gazette_id)
                
                if year_match and suffix_match:
                    year = year_match.group(0)
                    id_suffix = suffix_match.group(1)
                    pdf_url = f"{BASE_URL}WriteReadData/{year}/{id_suffix}.pdf"
                    filename = f"{gazette_id.replace('-', '_')}.pdf"
                    
                    # Check if already exists
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    if os.path.exists(filepath):
                        print(f"Skipping existing file: {filename}")
                        continue
                    
                    page_matches.append((pdf_url, filename))

            # 3. Download from current page matches
            for url, filename in page_matches:
                if downloaded_count >= MAX_DOWNLOADS:
                    break
                if await download_file(url, filename):
                    downloaded_count += 1

            if downloaded_count >= MAX_DOWNLOADS:
                print(f"Reached MAX_DOWNLOADS limit: {MAX_DOWNLOADS}")
                break
                
            # 4. Navigate to next page
            if current_page < max_page:
                next_page_num = current_page + 1
                print(f"Navigating to Page {next_page_num}...")
                
                # Find the link for the next page
                next_page_link = page.locator(f"#gvGazetteList a:text('{next_page_num}')").first
                if await next_page_link.count() > 0:
                    await next_page_link.click()
                    current_page = next_page_num
                else:
                    print(f"Could not find link for Page {next_page_num}. Ending.")
                    break
            else:
                print("No more pages left.")
                break

        await browser.close()
        print(f"Process complete. Total new files downloaded: {downloaded_count}")

if __name__ == "__main__":
    asyncio.run(main())
