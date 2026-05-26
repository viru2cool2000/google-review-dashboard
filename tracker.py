import requests
import json
import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

# ── Secrets ──────────────────────────────────────────────────────────────────
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID")

# ── Files ─────────────────────────────────────────────────────────────────────
COUNT_FILE = "reviews.json"
CSV_FILE   = "google_reviews.csv"

# ── Validate secrets ──────────────────────────────────────────────────────────
if not APIFY_TOKEN or not BOT_TOKEN or not CHAT_ID:
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
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ Apify API error: {e}")
    exit(1)

# ── Validate response ─────────────────────────────────────────────────────────
if not isinstance(data, list) or len(data) == 0:
    print("❌ Invalid or empty API response")
    exit(1)

place = data[0]

# ── Business details ──────────────────────────────────────────────────────────
business_name    = place.get("title", "Unknown")
current_reviews  = place.get("reviewsCount", 0)
rating           = place.get("totalScore", 0)

# ── Load old review count ─────────────────────────────────────────────────────
old_reviews = 0
if os.path.exists(COUNT_FILE):
    try:
        with open(COUNT_FILE, "r") as f:
            saved = json.load(f)
            old_reviews = saved.get("count", 0)
    except (json.JSONDecodeError, IOError):
        print("⚠️ Could not read reviews.json — starting fresh.")

# ── New reviews since last run ────────────────────────────────────────────────
new_reviews = max(0, current_reviews - old_reviews)

# ── IST timestamp ─────────────────────────────────────────────────────────────
current_time_ist = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p IST")

# ── Extract reviews ───────────────────────────────────────────────────────────
reviews = place.get("reviews", [])

# ── Save to CSV (append, no duplicates) ───────────────────────────────────────
file_exists = os.path.exists(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    if not file_exists:
        writer.writerow(["Date", "Customer Name", "Rating", "Review"])
    for review in reviews:
        writer.writerow([
            current_time_ist,
            review.get("name", "Unknown"),
            review.get("stars", ""),
            review.get("text", "").replace("\n", " ").strip()   # ← clean multiline text
        ])

print(f"✅ Saved {len(reviews)} reviews to {CSV_FILE}")

# ── Telegram message ──────────────────────────────────────────────────────────
message = (
    f"📍 *{business_name}*\n"
    f"⭐ Rating: {rating}\n"
    f"📝 Total Reviews: {current_reviews}\n"
    f"🆕 New Reviews Since Last Run: {new_reviews}\n"
    f"📅 {current_time_ist}"
)

print(message)

# ── Send to Telegram ──────────────────────────────────────────────────────────
try:
    tg_response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"        # ← enables bold/italics in message
        },
        timeout=30
    )
    tg_response.raise_for_status()
    print("✅ Telegram message sent")
except requests.exceptions.RequestException as e:
    print(f"❌ Telegram send failed: {e}")

# ── Save latest count ─────────────────────────────────────────────────────────
with open(COUNT_FILE, "w") as f:
    json.dump({"count": current_reviews}, f)

print("✅ Review count saved")
