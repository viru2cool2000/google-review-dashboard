```python
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

# Files
COUNT_FILE = "reviews.json"
CSV_FILE = "google_reviews.csv"

# Apify API URL
url = f"https://api.apify.com/v2/acts/compass~google-maps-extractor/run-sync-get-dataset-items?token={APIFY_TOKEN}"

# Payload
payload = {
    "searchStringsArray": [
        "Chandukaka Saraf Kalaburagi"
    ],
    "maxCrawledPlacesPerSearch": 1,
    "maxReviews": 10,
    "reviewsSort": "newest"
}

# Fetch data
response = requests.post(url, json=payload)
data = response.json()

# Validate response
if not isinstance(data, list) or len(data) == 0:
    print("Invalid API response")
    exit()

place = data[0]

# Business details
business_name = place.get("title", "Unknown")
current_reviews = place.get("reviewsCount", 0)
rating = place.get("totalScore", 0)

# Load old review count
old_reviews = 0

if os.path.exists(COUNT_FILE):
    try:
        with open(COUNT_FILE, "r") as file:
            saved = json.load(file)
            old_reviews = saved.get("count", 0)
    except:
        pass

# Calculate new reviews
new_reviews = current_reviews - old_reviews

if new_reviews < 0:
    new_reviews = 0

# IST Time
current_time_ist = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%d-%m-%Y %I:%M %p IST")

# Extract customer reviews
reviews = place.get("reviews", [])

# Save reviews to CSV
file_exists = os.path.exists(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    # Header
    if not file_exists:
        writer.writerow([
            "Date",
            "Customer Name",
            "Rating",
            "Review"
        ])

    # Rows
    for review in reviews:
        customer = review.get("name", "Unknown")
        stars = review.get("stars", "")
        text = review.get("text", "")

        writer.writerow([
            current_time_ist,
            customer,
            stars,
            text
        ])

# Telegram message
message = f"""
📍 {business_name}

⭐ Rating: {rating}
📝 Total Reviews: {current_reviews}
🆕 New Reviews: {new_reviews}

📅 {current_time_ist}
"""

print(message)

# Send Telegram
telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

telegram_response = requests.post(
    telegram_url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(telegram_response.text)

# Save latest count
with open(COUNT_FILE, "w") as file:
    json.dump({"count": current_reviews}, file)
```
