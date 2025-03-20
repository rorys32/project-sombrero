import json
import os
import time
import logging
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup  # Added missing import
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scrape_articles.log"), logging.StreamHandler()]
)

# Input and output paths
json_file = "ai_google_alerts.json"
archive_dir = "sombrero_archive"

# Create archive directory if it doesn’t exist
os.makedirs(archive_dir, exist_ok=True)

# User agent pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
]

# Load JSON data
try:
    with open(json_file, "r", encoding="utf-8") as f:
        alerts = json.load(f)
    logging.info(f"Loaded {len(alerts)} alerts from {json_file}")
except Exception as e:
    logging.error(f"Failed to load JSON: {e}")
    raise

# Function to extract the real URL from Google redirect
def get_real_url(google_url):
    try:
        parsed = urlparse(google_url)
        query = parse_qs(parsed.query)
        real_url = query.get("q", [google_url])[0]
        return real_url if real_url.startswith("http") else google_url
    except Exception as e:
        logging.warning(f"Couldn’t extract real URL from {google_url}: {e}")
        return google_url

# Scrape each article with Playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for i, alert in enumerate(alerts):
        google_url = alert["url"]
        real_url = get_real_url(google_url)  # Use the real URL
        title = alert["title"]
        date = alert["date"]
        safe_filename = f"{i}_{urlparse(real_url).netloc}_{date.replace(' ', '_').replace(':', '-')}.txt"
        filepath = os.path.join(archive_dir, safe_filename)

        # Skip if already archived
        if os.path.exists(filepath):
            logging.info(f"Skipping {title} (already archived) [{i+1}/{len(alerts)}]")
            continue

        # Randomize user agent
        user_agent = random.choice(USER_AGENTS)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()

        logging.info(f"Scraping {title} ({real_url}) [{i+1}/{len(alerts)}] with UA: {user_agent}")
        try:
            page.goto(real_url, timeout=30000)  # Navigate to real URL
            page.wait_for_load_state("networkidle")

            # Extract text content
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Remove unwanted elements
            for elem in soup(["script", "style", "iframe", "nav", "footer", "header", "aside"]):
                elem.decompose()

            # Broaden content extraction
            main_content = []
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'article']):
                text = tag.get_text(strip=True)
                if text and len(text) > 10:
                    main_content.append(text)

            logging.debug(f"Extracted {len(main_content)} content items")
            if main_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\nURL: {real_url}\nDate: {date}\n\n")
                    f.write("\n\n".join(main_content))
                logging.info(f"Saved simplified text to {filepath} [{i+1}/{len(alerts)}]")
            else:
                logging.warning(f"No meaningful content found for {title} [{i+1}/{len(alerts)}]")

            alert["archive_path"] = filepath
        except Exception as e:
            logging.warning(f"Failed to scrape {title} ({real_url}): {e} [{i+1}/{len(alerts)}]")
        
        context.close()
        time.sleep(2)

    browser.close()

# Save updated JSON with archive paths
updated_json = "ai_google_alerts_with_archive.json"
with open(updated_json, "w", encoding="utf-8") as f:
    json.dump(alerts, f, indent=4)
logging.info(f"Saved updated JSON with archive paths to {updated_json}")