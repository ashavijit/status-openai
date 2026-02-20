import json
import time
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



class StatusListener:

    def __init__(self, feeds, interval=60):
        self.feeds = feeds
        self.interval = interval
        self.seen = set()

    def fetch_provider(self, provider, url):

        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"[WARN] Invalid feed: {provider}")
            return

        for entry in feed.entries:

            uid = entry.get("id", entry.get("link"))

            if not uid or uid in self.seen:
                continue

            self.seen.add(uid)

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            title = entry.get("title", "Unknown Product")
            summary = entry.get("summary", "")

            status, message, components = format_status(summary)

            self.print_event(
                timestamp,
                provider,
                title,
                status,
                message,
                components
            )

    def print_event(
        self,
        timestamp,
        provider,
        product,
        status,
        message,
        components
    ):

        print(f"\n[{timestamp}] Provider: {provider}")
        print(f"Product: {product}")
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

    def start(self):

        print("Status Listener Started\n")

        while True:

            try:
                for provider, url in self.feeds.items():
                    self.fetch_provider(provider, url)

                time.sleep(self.interval)

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

    listener = StatusListener(feeds, interval)
    listener.start()


if __name__ == "__main__":
    main()