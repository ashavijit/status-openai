import json
import time
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup


CONFIG_FILE = "config.json"


def load_config(path=CONFIG_FILE):
    with open(path, "r") as f:
        return json.load(f)


def clean_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator="\n")

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    return lines


def format_status(summary_html):

    lines = clean_html(summary_html)

    status = "Unknown"
    message = []
    components = []

    reading_message = True

    for line in lines:

        low = line.lower()

        if low.startswith("status:"):
            status = line.replace("Status:", "").strip()
            continue

        if "affected components" in low:
            reading_message = False
            continue

        if not reading_message:
            components.append(line)
            continue

        message.append(line)

    return status, message, components


CACHE = {}
SEEN = set()


def fetch_provider(provider, url):

    headers = {}

    if url in CACHE:

        if CACHE[url].get("etag"):
            headers["If-None-Match"] = CACHE[url]["etag"]

        if CACHE[url].get("last_modified"):
            headers["If-Modified-Since"] = CACHE[url]["last_modified"]

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        print(f"[ERROR] {provider} request failed:", e)
        return

    if response.status_code == 304:
        return

    CACHE[url] = {
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified")
    }

    feed = feedparser.parse(response.content)

    if feed.bozo:
        print(f"[WARN] Invalid feed: {provider}")
        return

    for entry in feed.entries:

        uid = entry.get("id", entry.get("link"))

        if not uid or uid in SEEN:
            continue

        SEEN.add(uid)

        print_entry(provider, entry)


def print_entry(provider, entry):

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    title = entry.get("title", "Unknown Product")
    summary = entry.get("summary", "")

    status, message, components = format_status(summary)

    print(f"\n[{timestamp}] Provider: {provider}")
    print(f"Product: {title}")
    print(f"Status: {status}")

    if message:
        print("\nDetails:")
        for line in message:
            print(f"  - {line}")

    if components:
        print("\nAffected Services:")
        for comp in components:
            print(f"  - {comp}")

    print("-" * 60)


def start_listener(feeds, interval):

    print("Status Listener Started\n")

    while True:

        try:
            for provider, url in feeds.items():
                fetch_provider(provider, url)

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except Exception as e:
            print("[ERROR]", e)
            time.sleep(30)


def main():

    config = load_config()

    feeds = config.get("feeds", {})
    interval = config.get("check_interval", 60)

    if not feeds:
        print("No feeds configured.")
        return

    start_listener(feeds, interval)


if __name__ == "__main__":
    main()