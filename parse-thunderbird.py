import mailbox
import html
from bs4 import BeautifulSoup  # Install with `pip install beautifulsoup4`
import json
import csv
from email.header import decode_header
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parse_ai_alerts.log"),  # Save to file
        logging.StreamHandler()  # Also print to console
    ]
)

# Path to your Thunderbird INBOX mbox file
mbox_path = "/Users/ericclapton/Library/Thunderbird/Profiles/alotb7va.default-esr/ImapMail/imap.gmail-2.com/INBOX"

# Output files
json_output = "ai_google_alerts.json"
csv_output = "ai_google_alerts.csv"

# Open the mbox file
try:
    mbox = mailbox.mbox(mbox_path)
    logging.info(f"Successfully opened mbox file: {mbox_path}")
except Exception as e:
    logging.error(f"Failed to open mbox file: {e}")
    raise

# Store extracted data and counters
alerts_data = []
total_emails = 0
total_google_alerts = 0

# Decode email subject
def decode_subject(subject):
    decoded = decode_header(subject)
    return "".join([t[0].decode(t[1] or "utf-8") if isinstance(t[0], bytes) else t[0] for t in decoded])

# Process each email
logging.info("Starting email processing...")
for i, message in enumerate(mbox):
    total_emails += 1
    sender = message["from"] or ""
    logging.debug(f"Processing email {i+1}, sender: {sender}")

    if "googlealerts-noreply@google.com" not in sender:
        logging.debug(f"Skipping email {i+1}: Not from Google Alerts")
        continue

    total_google_alerts += 1
    subject = decode_subject(message["subject"] or "No Subject")
    alert_term = subject.replace("Google Alert - ", "").strip()
    logging.info(f"Found Google Alert with subject: {subject}, alert_term: {alert_term}")

    # Filter for alerts containing "that uses AI to" (with or without quotes)
    normalized_alert_term = alert_term.lower().replace('"', '')
    if "that uses ai to" not in normalized_alert_term:
        logging.info(f"Skipping alert: '{alert_term}' does not contain 'that uses AI to'")
        continue

    # Get HTML body
    html_body = ""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/html":
                html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                break
    else:
        if message.get_content_type() == "text/html":
            html_body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

    if not html_body:
        logging.warning(f"No HTML content found in email {i+1}: {subject}")
        continue

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_body, "html.parser")
    links = soup.find_all("a")
    logging.debug(f"Found {len(links)} links in email {i+1}")

    # Extract title, URL, and synopsis
    for link in links:
        url = link.get("href")
        title = link.get_text(strip=True)
        if not url or not title or "google.com/url" not in url:
            logging.debug(f"Skipping link in email {i+1}: Not a valid alert link (URL: {url})")
            continue

        # Synopsis is typically in the next <div> or <font> or <p> after the link
        synopsis = ""
        next_elem = link.find_next(["div", "font", "p"])
        if next_elem:
            synopsis = next_elem.get_text(strip=True)
        else:
            logging.warning(f"No synopsis found for link '{title}' in email {i+1}")

        # Clean up data and fix spacing after "that uses AI to"
        title = html.unescape(title)
        synopsis = html.unescape(synopsis)
        if "that uses AI to" in synopsis:
            synopsis = synopsis.replace("that uses AI to", "that uses AI to ")

        # Add to data structure
        alerts_data.append({
            "alert_term": alert_term,
            "title": title,
            "url": url,
            "synopsis": synopsis
        })
        logging.info(f"Added alert: {title} (URL: {url})")

# Log summary
logging.info(f"Summary: Evaluated {total_emails} total emails, found {total_google_alerts} Google Alerts, saved {len(alerts_data)} 'that uses AI to' alerts")

# Save to JSON
with open(json_output, "w", encoding="utf-8") as json_file:
    json.dump(alerts_data, json_file, indent=4, ensure_ascii=False)
logging.info(f"Saved {len(alerts_data)} 'that uses AI to' alerts to {json_output}")

# Save to CSV
with open(csv_output, "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["alert_term", "title", "url", "synopsis"])
    writer.writeheader()
    writer.writerows(alerts_data)
logging.info(f"Saved {len(alerts_data)} 'that uses AI to' alerts to {csv_output}")