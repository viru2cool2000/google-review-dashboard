import requests
import json
import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

# ── Secrets ───────────────────────────────────────────────────────────────────
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID")

# ── Files ─────────────────────────────────────────────────────────────────────
COUNT_FILE = "reviews.json"
CSV_FILE   = "google_reviews.csv"

# ── Validate secrets ──────────────────────────────────────────────────────────
if not all([APIFY_TOKEN, BOT_TOKEN, CHAT_ID]):
    print("❌ Missing environment variables. Check APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.")
    exit(1)

# ── Apify request ─────────────────────────────────────────────────────────────
url = (
    "https://api.apify.com/v2/acts/compass~google-maps-extractor/"
    f"run-sync-get-dataset-items?token={APIFY_TOKEN}"
)

payload = {
    "searchStringsArray": ["Chandukaka Saraf Kalaburagi"],
    "maxCrawledPlacesPerSearch": 1,
    "maxReviews": 10,
    "reviewsSort": "newest"
}

try:
    with open(CSV_FILE, "rb") as f:
        file_response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={
                "chat_id": CHAT_ID,
                "caption": message,
                "parse_mode": "Markdown"
            },
            files={"document": (CSV_FILE, f, "text/csv")},
            timeout=30
        )
    file_response.raise_for_status()
    print("✅ CSV sent to Telegram")
except FileNotFoundError:
    print("❌ CSV file not found")
except requests.exceptions.RequestException as e:
    print(f"❌ Telegram send failed: {e}")
