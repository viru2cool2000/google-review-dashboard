import requests
import json
import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

# Secrets
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

COUNT_FILE = "reviews.json"
CSV_FILE = "google_reviews.csv"

if not all([APIFY_TOKEN, BOT_TOKEN, CHAT_ID]):
    print("Missing environment variables.")
    exit(1)

# Apify request
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
    print("Apify API error: " + str(e))
    exit(1)

if not isinstance(data, list) or len(data) == 0:
    print("Invalid or empty API response")
    exit(1)

place = data[0]

# Business details
business_name = place.get("title", "Unknown")
current_reviews = place.get("reviewsCount", 0)
rating = place.get("totalScore", 0)

# Load old review count
old_reviews = 0
if os.path.exists(COUNT_FILE):
    try:
        with open(COUNT_FILE, "r") as f:
            saved = json.load(f)
            old_reviews = saved.get("count", 0)
    except (json.JSONDecodeError, IOError):
        print("Could not read reviews.json, starting fresh.")

new_reviews = max(0, current_reviews - old_reviews)

# IST timestamp
current_time_ist = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p IST")

# Extract reviews
reviews = place.get("reviews", [])

# Load existing Review IDs
existing_ids = set()
if os.path.exists(CSV_FILE):
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ids.add(row["Review ID"])
    except (IOError, KeyError):
        pass

# Save to CSV
file_exists = os.path.exists(CSV_FILE)
new_saved = 0

with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    if not file_exists:
        writer.writerow(["Review ID", "Date", "Customer Name", "Rating", "Review"])
    for review in reviews:
        review_id = review.get("reviewId") or review.get("id", "")
        if review_id in existing_ids:
            continue
        writer.writerow([
            review_id,
            current_time_ist,
            (review.get("name") or "Unknown"),
            (review.get("stars") or ""),
            (review.get("text") or "").replace("\n", " ").strip()
        ])
        existing_ids.add(review_id)
        new_saved += 1

print("New reviews saved: " + str(new_saved))

# Check file exists
if os.path.exists(CSV_FILE):
    print("File exists, size: " + str(os.path.getsize(CSV_FILE)) + " bytes")
else:
    print("CSV file not found")
    exit(1)

# Telegram message
message = (
    "Business: " + business_name + "\n"
    "Rating: " + str(rating) + "\n"
    "Total Reviews: " + str(current_reviews) + "\n"
    "New Reviews: " + str(new_reviews) + "\n"
    "Rows Added: " + str(new_saved) + "\n"
    "Time: " + current_time_ist
)

print(message)

# Send CSV to Telegram
try:
    with open(CSV_FILE, "rb") as f:
        file_response = requests.post(
            "https://api.telegram.org/bot" + BOT_TOKEN + "/sendDocument",
            data={
                "chat_id": CHAT_ID,
                "caption": message
            },
            files={"document": (CSV_FILE, f, "text/csv")},
            timeout=30
        )
    file_response.raise_for_status()
    print("CSV sent to Telegram successfully")
except FileNotFoundError:
    print("CSV file not found")
except requests.exceptions.RequestException as e:
    print("Telegram send failed: " + str(e))

# Save latest count
with open(COUNT_FILE, "w") as f:
    json.dump({"count": current_reviews}, f)

print("Review count saved")
