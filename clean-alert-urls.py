import json
import csv
from urllib.parse import urlparse, parse_qs
import logging
import os

# Set up logging with DEBUG level for detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("clean_alert_urls.log"), logging.StreamHandler()]
)

# Function to extract the real URL from a Google redirect
def get_real_url(google_url):
    if not google_url.startswith("https://www.google.com/url"):
        logging.debug(f"URL is not a Google redirect, keeping as-is: {google_url}")
        return google_url
    try:
        parsed = urlparse(google_url)
        query = parse_qs(parsed.query)
        logging.debug(f"Query parameters: {query}")
        real_url = query.get("url", None)  # Changed from 'q' to 'url'
        if real_url:
            real_url = real_url[0]  # Take the first value
            logging.debug(f"Extracted real URL: {google_url} -> {real_url}")
            return real_url if real_url.startswith("http") else google_url
        else:
            logging.warning(f"No 'url' parameter found in {google_url}, keeping original")
            return google_url
    except Exception as e:
        logging.error(f"Error parsing URL {google_url}: {e}")
        return google_url

# Files to process
input_json_files = ["ai_google_alerts.json", "pilatus_alerts.json"]
input_csv_files = ["ai_google_alerts.csv", "pilatus_alerts.csv"]
output_dir = "data/sanitized"
output_json_suffix = "_cleaned.json"
output_csv_suffix = "_cleaned.csv"

# Create output directory if it doesn’t exist
os.makedirs(output_dir, exist_ok=True)

# Process JSON files
for json_file in input_json_files:
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Loaded {len(data)} alerts from {json_file}")

        # Clean URLs in the data
        for alert in data:
            original_url = alert["url"]
            cleaned_url = get_real_url(original_url)
            alert["url"] = cleaned_url
            if original_url != cleaned_url:
                logging.info(f"Cleaned URL: {original_url} -> {cleaned_url}")
            else:
                logging.debug(f"No change for URL: {original_url}")

        # Save cleaned JSON in data/sanitized
        output_json = os.path.join(output_dir, os.path.basename(json_file).replace(".json", output_json_suffix))
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Saved cleaned data to {output_json}")
    except Exception as e:
        logging.error(f"Failed to process {json_file}: {e}")

# Process CSV files
for csv_file in input_csv_files:
    try:
        # Read CSV
        with open(csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        logging.info(f"Loaded {len(rows)} alerts from {csv_file}")

        # Clean URLs in the rows
        for row in rows:
            original_url = row["url"]
            cleaned_url = get_real_url(original_url)
            row["url"] = cleaned_url
            if original_url != cleaned_url:
                logging.info(f"Cleaned URL: {original_url} -> {cleaned_url}")
            else:
                logging.debug(f"No change for URL: {original_url}")

        # Save cleaned CSV in data/sanitized
        output_csv = os.path.join(output_dir, os.path.basename(csv_file).replace(".csv", output_csv_suffix))
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logging.info(f"Saved cleaned data to {output_csv}")
    except Exception as e:
        logging.error(f"Failed to process {csv_file}: {e}")